import numpy as np
from pathlib import Path

from utils import BrainData
from preprocess import preprocess_data
from searchlight import build_searchlight_indices
from rdm import build_rdm, build_model_rdm, calculate_rsa_score


def main(data_dpath, output_fpath, radius):
    print(f'Reading data from {data_dpath}')
    bd = BrainData.from_directory(data_dpath, apply_mask=False)

    print('Preprocessing')
    bd = preprocess_data(bd)

    print('Starting searchlight analysis')
    bd.sort_by_labels()
    model_rdm = build_model_rdm(bd.labels)
    sl_points_iv = build_searchlight_indices(radius=radius)
    print(f'Searchlight has radius {radius} '
          f'and {sl_points_iv.shape[0]} points')

    data_gt = bd.data
    Ng_v = data_gt.shape[:-1]
    rsa_data_g = np.zeros(Ng_v)
    points_iv = np.argwhere(bd.mask == 1)
    Ni = points_iv.shape[0]
    for i, origin_v in enumerate(points_iv):
        # XXX This is a terribly slow loop. Vectorizing should help

        # Index list without out-of-bounds indices
        indices_iv = (origin_v + sl_points_iv)
        flt_i = np.logical_and(np.all(indices_iv >= 0, axis=1),
                               np.all(indices_iv < Ng_v, axis=1))
        indices_iv = indices_iv[flt_i]

        # Process data inside the searchlight
        sl_data_gt = data_gt[tuple(indices_iv.T)]
        rdm = build_rdm(sl_data_gt)
        rsa = calculate_rsa_score(rdm, model_rdm)
        rsa_data_g[tuple(origin_v)] = rsa

        print(f'\r{(i + 1) / Ni * 100:.2f}% done', end='')

    print()
    print(f'Writing RSA data to {output_fpath}')
    rsa_bd = BrainData(data=rsa_data_g[..., np.newaxis], mask=bd.mask,
                       labels=np.array(['']), chunks=np.array([0]),
                       affine=bd.affine)
    rsa_bd.write(output_fpath)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('data_dpath', type=Path)
    parser.add_argument('output_fpath', type=Path)
    parser.add_argument('--radius', type=int, default=2)
    args = parser.parse_args()

    kwargs = vars(args)
    main(**kwargs)
