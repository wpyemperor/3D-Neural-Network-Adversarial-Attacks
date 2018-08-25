import tensorflow as tf

def remove_outliers_fn(x, top_k = 10, num_std = 1.0):
    dists = x[:, tf.newaxis] - x[:, :, tf.newaxis]
    dists = tf.linalg.norm(dists, axis = 3)
    
    diag = tf.eye(tf.shape(x)[1], batch_shape = [tf.shape(x)[0]])
    dists = tf.where(diag > 0.0, tf.fill(tf.shape(dists), float("inf")), dists)
    dists = tf.nn.top_k(dists * -1.0, k = top_k, sorted = False)[0] * -1.0
    
    dists = tf.reduce_mean(dists, axis = 2)
    avg, var = tf.nn.moments(dists, axes = [1], keep_dims = True)
    std = num_std * tf.sqrt(var)
    
    remove = dists > avg + std
    idx = tf.argmin(tf.to_float(remove), axis = 1)
    one_hot = tf.one_hot(idx, tf.shape(x)[1])
    replace = tf.reduce_sum(x * one_hot[:, :, tf.newaxis], axis = 1, keep_dims = True)
    x = tf.where(remove[:, :, tf.newaxis] & tf.fill(tf.shape(x), True), replace + tf.zeros_like(x), x)

    return tf.stop_gradient(x)