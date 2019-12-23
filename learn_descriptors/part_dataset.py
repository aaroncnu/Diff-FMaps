'''
    Dataset for shapenet part segmentaion.
'''

import os
import os.path
import json
import numpy as np
import sys
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, '/home/marie-julie/projects/test_pointnet/pyFuncMap/utils')
import MeshProcess
from scipy.io import loadmat
from plyfile import PlyData
import trimesh

def pc_normalize(pc):
    """ pc: NxC, return NxC """
    l = pc.shape[0]
    centroid = np.mean(pc, axis=0)
    pc = pc - centroid
    m = np.max(np.sqrt(np.sum(pc**2, axis=1)))
    pc = pc / m
    return pc

def pc_normalize_area(pc,triv):
    area = MeshProcess.compute_real_mesh_surface_area(pc, triv)
    alpha = 1.66/area
    pc = pc*np.sqrt(alpha)
    centroid = np.mean(pc, axis=0)
    pc = pc - centroid
    return pc

def rotate_point_cloud(batch_data_shuffled, batch_data ):
    """ Randomly rotate the point clouds to augument the dataset
        rotation is per shape based along up direction
        Input:
          BxNx3 array, original batch of point clouds
        Return:
          BxNx3 array, rotated batch of point clouds
    """
    rotated_data = np.zeros(batch_data.shape, dtype=np.float32)
    rotated_data_shuffled = np.zeros(batch_data.shape, dtype=np.float32)
    for k in xrange(batch_data.shape[0]):
        rotation_angle = np.random.uniform() * 2 * np.pi
        cosval = np.cos(rotation_angle)
        sinval = np.sin(rotation_angle)
        rotation_matrix = np.array([[cosval, 0, sinval],
                                    [0, 1, 0],
                                    [-sinval, 0, cosval]])
        shape_pc = batch_data[k, ...]
        shape_pc_shuffled = batch_data_shuffled[k, ...]
        rotated_data[k, ...] = np.dot(shape_pc.reshape((-1, 3)), rotation_matrix)
        rotated_data_shuffled[k, ...] = np.dot(shape_pc_shuffled.reshape((-1, 3)), rotation_matrix)
    return rotated_data_shuffled, rotated_data



class PartDataset():
    def __init__(self, root, npoints = 2500,  split='train', normalize=True, normalize_area=False,n_basis = 100):
        self.normalize = normalize
        self.npoints = npoints
        self.normalize_area = normalize_area
        print('loading...')
        if split =="train":
            print('loading train')
            self.data = np.load(os.path.join(root, "dfaust_surreal_shapes.npy"))
            print('loading train basis')
            self.basis = np.load(os.path.join(root, "dfaust_surreal_basis.npy"))
            print('loading train area')
            self.area =  np.load(os.path.join(root, "dfaust_surreal_area.npy"))
            print('loading train curv')
            self.curv =  np.load(os.path.join(root, "dfaust_surreal_curv.npy"))

            self.data = self.data[:2000]
            self.basis = self.basis[:2000]
            self.area = self.area[:2000]
        elif split =="test":
            print('loading test shapes')
            self.data = np.load(os.path.join(root, "dfaust_surreal_shapes_test.npy"))
            print('loading test basis')
            self.basis = np.load(os.path.join(root, "dfaust_surreal_basis_test.npy"))
            print('loading test area')
            self.area = np.load(os.path.join(root, "dfaust_surreal_area_diag_test.npy"))
            self.area = np.array([np.diag(x) for x in self.area])
            print('loading test curv')
            self.curv = np.load(os.path.join(root, "dfaust_surreal_curv_test.npy"))

        self.basis = self.basis[:,:,:n_basis]
        EDGES_PATH = os.path.join(root,"template.ply")
        self.part_labels = np.load(os.path.join(root,"part_labels.npy"))
        plydata = PlyData.read(EDGES_PATH)
        FACES = plydata['face']
        FACES = np.array([FACES[i][0] for i in range(FACES.count)])
        mesh = trimesh.Trimesh(self.data[0],FACES, process = False)
        self.laplacian = np.eye(1000)-trimesh.smoothing.laplacian_calculation(mesh).todense()
        print('data loaded ...')

    def __getitem__(self, index):
        point_set = self.data[index]
        choice = np.random.choice(len(point_set), self.npoints, replace=False)
        #choice = range(1000)
        point_set_shuffled = point_set[choice, :]
        basis_shuffled = self.basis[index][choice, :]
        area_shuffled = np.diag(self.area[index].diagonal()[choice])
        curv_shuffled = self.curv[index][choice]
        return point_set_shuffled,basis_shuffled, area_shuffled, curv_shuffled,point_set, choice

    def __len__(self):
        return len(self.data)
