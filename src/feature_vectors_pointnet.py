import numpy as np
import tensorflow as tf
import adversarial_utils
import os
import sys
import argparse
import importlib
working_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(working_dir, "models"))
sys.path.append(os.path.join(working_dir, "utils"))
from collections import defaultdict

parser = argparse.ArgumentParser(description = "Gets the feature vector for PointNet.", formatter_class = argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("--checkpoint", default = "log/model.ckpt", help = "Path to the model's checkpoint file.")
parser.add_argument("--data", help = "Input data, a Numpy file.")
parser.add_argument("--output", default = "feature_vectors", help = "Output path.")
parser.add_argument("--class-names", default = "data/modelnet40_ply_hdf5_2048/shape_names.txt", help = "Text file containing a list of class names.")
parser.add_argument("--num-objects", type = int, default = 1000000000, help = "Use the first few objects. Specify a very large number to use all objects.")
args = parser.parse_args()
print(args)

model = importlib.import_module("pointnet_cls")
class_names = [line.rstrip() for line in open(args.class_names)]

with np.load(args.data) as file:
    data_x_original = file["x_original"][:args.num_objects]
    data_x_adv = file["x_adv"][:args.num_objects]
    labels = file["labels"][:args.num_objects]
    pred_adv = file["pred_adv"][:args.num_objects]

x_pl, _ = model.placeholder_inputs(1, data_x_original.shape[1])

is_training = tf.placeholder(tf.bool, shape = [])

def model_loss_fn(x, t):
    with tf.variable_scope(tf.get_variable_scope(), reuse = tf.AUTO_REUSE):
        y, end_points = model.get_model(x, is_training)
    if t is None:
        loss = None
    else:
        loss = model.get_loss(y, t, end_points)
    return y, loss

features_original, features_adv = adversarial_utils.get_feature_vectors(args.checkpoint, x_pl, model_loss_fn, data_x_original, data_x_adv, class_names, extra_feed_dict = {is_training: False})

def print_per_class(per_class):
    for i, val in enumerate(per_class):
        print("%d, %s: %.3f" % (i, class_names[i], val))

counts = np.zeros(len(class_names))
np.add.at(counts, labels, 1)
zero = counts == 0.0
counts[zero] = 1.0

diff = features_adv - features_original
diff_norm = np.linalg.norm(diff, axis = 1)

print("Average L2 norms of feature vector changes: %.3f" % np.mean(diff_norm))

per_class = np.zeros(len(class_names))
np.add.at(per_class, labels, diff_norm)
per_class[zero] = 0.0
per_class = per_class / counts

print("Average L2 norms of feature vector changes per class:")
print_per_class(per_class)

percent_pos = np.sum(diff > 0.0, axis = 1) / float(diff.shape[1])
percent_neg = np.sum(diff < 0.0, axis = 1) / float(diff.shape[1])

print("Average %% positive change: %.3f" % np.mean(percent_pos))
print("Average %% negative change: %.3f" % np.mean(percent_neg))

per_class_pos = np.zeros(len(class_names))
np.add.at(per_class_pos, labels, percent_pos)
per_class_pos[zero] = 0.0
per_class_pos = per_class_pos / counts

per_class_neg = np.zeros(len(class_names))
np.add.at(per_class_neg, labels, percent_neg)
per_class_neg[zero] = 0.0
per_class_neg = per_class_neg / counts

print("Average % positive change per class:")
print_per_class(per_class_pos)

print("Average % negative change per class:")
print_per_class(per_class_neg)

print("Average dimension change %.3f" % np.mean(diff))

per_class = np.zeros(len(class_names))
np.add.at(per_class, labels, np.mean(diff, axis = 1))
per_class[zero] = 0.0
per_class = per_class / counts

print("Average dimension per class:")
print_per_class(per_class)

avg_diff = np.mean(diff, axis = 0)
print("Average change per dimension, min %.3f, max %.3f" % (np.min(avg_diff), np.max(avg_diff)))

pair_dist_original = np.zeros((len(class_names), len(class_names)))
pair_dist_adv = np.zeros((len(class_names), len(class_names)))
pair_dist_pred_adv_original = np.zeros((len(class_names), len(class_names)))
pair_dist_pred_adv = np.zeros((len(class_names), len(class_names)))
pair_counts = np.zeros((len(class_names), len(class_names)))
pair_counts_pred_adv = np.zeros((len(class_names), len(class_names)))
mask = np.zeros((len(class_names), len(class_names)))
for i in range(len(labels)):
    for j in range(len(labels)):
        pair_dist_original[labels[i]][labels[j]] += np.linalg.norm(features_original[i] - features_original[j])
        pair_dist_adv[labels[i]][labels[j]] += np.linalg.norm(features_adv[i] - features_original[j])
        pair_dist_pred_adv_original[pred_adv[i]][labels[j]] += np.linalg.norm(features_original[i] - features_original[j])
        pair_dist_pred_adv[pred_adv[i]][labels[j]] += np.linalg.norm(features_adv[i] - features_original[j])
        pair_counts[labels[i]][labels[j]] += 1
        pair_counts_pred_adv[pred_adv[i]][labels[j]] += 1

pair_dist_original = np.array(pair_dist_original)
pair_dist_adv = np.array(pair_dist_adv)
pair_counts = np.array(pair_counts)
pair_dist_pred_adv_original = np.array(pair_dist_pred_adv_original)
pair_dist_pred_adv = np.array(pair_dist_pred_adv)
pair_counts_pred_adv = np.array(pair_counts_pred_adv)
mask[labels, pred_adv] = 1.0

pair_dist_original[pair_counts == 0.0] = 0.0
pair_dist_adv[pair_counts == 0.0] = 0.0
pair_dist_pred_adv_original[pair_counts_pred_adv == 0.0] = 0.0
pair_dist_pred_adv[pair_counts_pred_adv == 0.0] = 0.0
pair_counts[pair_counts == 0.0] = 1.0
pair_counts_pred_adv[pair_counts_pred_adv == 0.0] = 1.0

pair_dist_original = pair_dist_original / pair_counts
pair_dist_adv = pair_dist_adv / pair_counts
pair_dist_pred_adv_original = pair_dist_pred_adv_original / pair_counts_pred_adv
pair_dist_pred_adv = pair_dist_pred_adv / pair_counts_pred_adv

adversarial_utils.heatmap(pair_dist_original, os.path.join(args.output, "original_dist.png"), "Original", "Original", class_names = class_names, percentages = False, annotate = False)
adversarial_utils.heatmap(pair_dist_adv, os.path.join(args.output, "adversarial_dist.png"), "Adversarial", "Original", class_names = class_names, percentages = False, annotate = False)
adversarial_utils.heatmap(pair_dist_adv - pair_dist_original, os.path.join(args.output, "adversarial_dist_change.png"), "Adversarial", "Original", class_names = class_names, percentages = False, annotate = False)
adversarial_utils.heatmap((pair_dist_adv - pair_dist_original) * mask, os.path.join(args.output, "adversarial_dist_relevant_change.png"), "Adversarial", "Original", class_names = class_names, percentages = False, annotate = False)

adversarial_utils.heatmap(pair_dist_pred_adv_original, os.path.join(args.output, "original_pred_adv_dist.png"), "Original", "Original", class_names = class_names, percentages = False, annotate = False)
adversarial_utils.heatmap(pair_dist_pred_adv, os.path.join(args.output, "adversarial_pred_adv_dist.png"), "Adversarial", "Original", class_names = class_names, percentages = False, annotate = False)
adversarial_utils.heatmap(pair_dist_pred_adv - pair_dist_pred_adv_original, os.path.join(args.output, "adversarial_pred_adv_dist_change.png"), "Adversarial", "Original", class_names = class_names, percentages = False, annotate = False)

def kth_max_freq(a, kth):
    res = defaultdict(int)
    max_idx = np.argpartition(np.abs(a), kth = -kth - 1, axis = 1)[:, -kth - 1]
    for i in max_idx:
        res[i] += 1
    return res

print("Number of times a dimension changes the most:")
print(kth_max_freq(diff, 0))

print("\nNumber of times a dimension changes second most:")
print(kth_max_freq(diff, 1))

print("\nNumber of times a dimension changes third most:")
print(kth_max_freq(diff, 2))