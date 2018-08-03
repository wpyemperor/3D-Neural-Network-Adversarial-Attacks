import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

load_path = "point_clouds/succeeded_point_clouds_eps_2_0.npz"
idx = 0
num_points_max = 1024
triangle_mesh = False

plt.figure(figsize = (12, 7))
plt.subplot(111, projection = "3d")

if load_path[-3:] == "npy":
    xs, ys, zs = np.load(load_path)[:num_points_max].T
elif load_path[-3:] == "npz":
    file = np.load(load_path)

    if "x_adv" in file:
        points, labels = file["x_adv"], file["labels"]
    else:
        points, labels = file["points"], file["labels"]
    
    if "faces" in file:
        faces = file["faces"]
    else:
        print("No triangular faces found in file!")
        triangle_mesh = False
    
    print("Label: %s" % labels[idx])

    xs, ys, zs = points[idx][:num_points_max].T
    
    if triangle_mesh:
        faces = faces[idx][:num_points_max, :3, [0, 2, 1]]
        unique = np.unique(faces.reshape(-1, faces.shape[-1]), axis = 0)
        triangles = np.empty(shape = (num_points_max, 3))

        for i in range(num_points_max):
            for j in range(3):
                k, = np.where(np.all(unique == faces[i][j], axis = 1))
                triangles[i][j] = k
        
        plt.gca().plot_trisurf(*unique.T, triangles = triangles)

print("Number of points: %d" % len(xs))
norm = np.linalg.norm(np.stack([xs, ys, zs], axis = 1), axis = 1)
print("Maximum L2 norm: %.3f" % np.max(norm))

plt.gca().scatter(xs, ys, zs, zdir = "y", s = 5)
plt.axis("scaled")

plt.gca().set_xlim(-2, 2)
plt.gca().set_ylim(-2, 2)
plt.gca().set_zlim(-2, 2)
plt.gca().view_init(0, 0)
plt.subplots_adjust(left = 0, bottom = 0, right = 1, top = 1, wspace = 0, hspace = 0)

plt.show()