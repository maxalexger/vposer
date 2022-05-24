# -*- coding: utf-8 -*-
"""
Created on Mon May 23 11:58:44 2022

@author: G.Marrazzo
"""

import numpy as np
from pathlib import Path
import os
import mat73
from voxelwise_tutorials.io import load_hdf5_array
from sklearn.model_selection import check_cv
from voxelwise_tutorials.utils import generate_leave_one_run_out
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from voxelwise_tutorials.delayer import Delayer
from himalaya.backend import set_backend
from himalaya.kernel_ridge import MultipleKernelRidgeCV
from himalaya.kernel_ridge import Kernelizer
from sklearn import set_config
from himalaya.kernel_ridge import ColumnKernelizer
from himalaya.scoring import r2_score_split 
from himalaya.scoring import r2_score
from himalaya.scoring import correlation_score_split 
from himalaya.scoring import correlation_score 
from matplotlib import pyplot as plt
import scipy.io
from himalaya.viz import plot_alphas_diagnostic


#import h5py

#with h5py.File(file_name, "r") as f:
    # List all groups
    #print("Keys: %s" % f.keys())
    #a_group_key = list(f.keys())[0]

    # Get the data
    #data = list(f[a_group_key])
    
data_folder = Path("/home/magehrke/data/")
model_folder = os.path.join(data_folder, 'Main_effect')
resdir = os.path.join(data_folder, "Himalaya")
if not os.path.exists(resdir):
    os.mkdir(resdir)
    
    
name = ["_data_python.mat"]
mod_name = "_data_python_transform_0"
subj = ["Fake_Sit_gabor_kp2d_kp3d"]
feature_names = ["S_it_output", 'VAE_dec', 'VAE_enc', 'VAEparam', "gabor", "kp2d", "kp3d"]


resmodstr='_'.join([feats for feats in feature_names])



data3 = mat73.loadmat(os.path.join(model_folder, 'hrf.mat'))
hrf = np.asarray(data3['hrf'])
data5 = mat73.loadmat('training_runs_onsets.mat')
run_onset = np.asarray((data5['onset']))
run_onset = run_onset.astype(dtype='int')
# data=[]
# for i in model:
#     string_mod = i+mod_name[0]
#     file_mod=data_folder / string_mod
#     data.append(mat73.loadmat(file_mod))
for s in subj:
        string_data = ''.join([s,name[0]])
        file_data = os.path.join(data_folder,string_data)
        print(string_data)
        data4= mat73.loadmat(file_data)
            
        print(resmodstr)

        cv_scores_split = []
        cv_scores=[]
        corr_tot=[]
        corr_scores_split = []
        for f in range(1):
            Ytrain_cv= np.asarray(data4['Ytrain'][f]).squeeze()
                
            Ytest_cv= np.asarray(data4['Ytest'][f]).squeeze()
            
            Ytrain_cv -= Ytrain_cv.mean(0)
            Ytrain_cv /= Ytrain_cv.std(0)
            Ytest_cv -= Ytest_cv.mean(0)
            Ytest_cv /= Ytest_cv.std(0)
            Xs_train = []
            Xs_test = []
            n_features_list = []
            for feature_space in feature_names:
                string_mod = feature_space+mod_name[0]
                file_name = os.path.join(model_folder, f"{feature_space}"f"{mod_name}_cv"f"{f+1}.h5")        
                Xi_train = (load_hdf5_array(file_name, key="X_train")).T
                # for i in range(Xi_train.shape[1]):
                #     Xi_train[:,i] = np.convolve(Xi_train[:,i],hrf)[0:Xi_train.shape[0]]
                Xi_test = (load_hdf5_array(file_name, key="X_test")).T
                # for i in range(Xi_test.shape[1]):
                #     Xi_test[:,i] = np.convolve(Xi_test[:,i],hrf)[0:Xi_test.shape[0]]
                Xs_train.append(Xi_train.astype(dtype="float32"))
                Xs_test.append(Xi_test.astype(dtype="float32"))
                n_features_list.append(Xi_train.shape[1])
            
        # concatenate the feature spaces
            X_train = np.concatenate(Xs_train, 1)
            X_test = np.concatenate(Xs_test, 1)
            
            n_samples_train = X_train.shape[0]
            cv = generate_leave_one_run_out(n_samples_train, run_onset[0,:])
            cv = check_cv(cv)  # copy the cross-validation splitter into a reusable 
            backend = set_backend("torch_cuda", on_error="warn")
            #backend = set_backend("cupy", on_error="warn")
    
            
            # Here we will use the "random_search" solver.
            solver = "random_search"
 
            
            # We can check its specific parameters in the function docstring:
            # solver_function = MultipleKernelRidgeCV.ALL_SOLVERS[solver]
            # print("Docstring of the function %s:" % solver_function.__name__)
            # print(solver_function.__doc__)
            
            ###############################################################################
            # The hyperparameter random-search solver separates the hyperparameters into a
            # shared regularization ``alpha`` and a vector of positive kernel weights which
            # sum to one. This separation of hyperparameters allows to explore efficiently
            # a large grid of values for ``alpha`` for each sampled kernel weights vector.
            #
            # We use *20* random-search iterations to have a reasonably fast example. To
            # have better results, especially for larger number of feature spaces, one
            # might need more iterations. (Note that there is currently no stopping
            # criterion in the random-search method.)
            n_iter = 20
            # n_iter=120
            alphas = np.logspace(0, 10, 30)
            # alphas         = np.logspace(0,4,11)
    
            
            ###############################################################################
            # Batch parameters, used to reduce the necessary GPU memory. A larger value
            # will be a bit faster, but the solver might crash if it is out of memory.
            # Optimal values depend on the size of your dataset.
            # n_targets_batch = 200
            # n_alphas_batch = 5
            # n_targets_batch_refit = 200
            n_targets_batch = 1000
            n_alphas_batch = 20
            n_targets_batch_refit = 200
            
            ###############################################################################
            # We put all these parameters in a dictionary ``solver_params``, and define
            # the main estimator ``MultipleKernelRidgeCV``.
            
            solver_params = dict(n_iter=n_iter, alphas=alphas,
                                  n_targets_batch=n_targets_batch,
                                  n_alphas_batch=n_alphas_batch,
                                  n_targets_batch_refit=n_targets_batch_refit)
                       # Here we will use the "Hyper_gradient" solver.
           
            
            # solver_params = dict(n_iter=5, alphas=np.logspace(-10, 10, 41))
    
            model_1 = MultipleKernelRidgeCV(kernels="precomputed", solver=solver,
                                    solver_params=solver_params, random_state=42,cv=cv)
            
            # mkr_model = MultipleKernelRidgeCV(kernels="precomputed", solver=solver,
            #                                   solver_params=solver_params, cv=cv)
            
            ###############################################################################
            # We need a bit more work than in previous examples before defining the full
            # pipeline, since the banded ridge model requires `multiple` precomputed
            # kernels, one for each feature space. To compute them, we use the
            # ``ColumnKernelizer``, which can create multiple kernels from different
            # column of your features array. ``ColumnKernelizer`` works similarly to
            # ``scikit-learn``'s ``ColumnTransformer``, but instead of returning a
            # concatenation of transformed features, it returns a stack of kernels,
            # as required in ``MultipleKernelRidgeCV(kernels="precomputed")``.
            
            ###############################################################################
            # First, we create a different ``Kernelizer`` for each feature space.
            # Here we use a linear kernel for all feature spaces, but ``ColumnKernelizer``
            # accepts any ``Kernelizer``, or ``scikit-learn`` ``Pipeline`` ending with a
            # ``Kernelizer``.
           
            set_config(display='diagram')  # requires scikit-learn 0.23
            
            preprocess_pipeline = make_pipeline(
                StandardScaler(with_mean=True, with_std=True),
                Delayer(delays=[1,2,3,4,5,6,7,8]),
                Kernelizer(kernel="linear"),
            )
            
            # preprocess_pipeline = make_pipeline(
            #     StandardScaler(with_mean=True, with_std=False),
            #     Delayer(delays=[0]),
            #     Kernelizer(kernel="linear"),
            # )
            # preprocess_pipeline
            
            ###############################################################################
            # The column kernelizer applies a different pipeline on each selection of
            # features, here defined with ``slices``.
            
            # Find the start and end of each feature space in the concatenated ``X_train``.
            start_and_end = np.concatenate([[0], np.cumsum(n_features_list)])
            slices = [
                slice(start, end)
                for start, end in zip(start_and_end[:-1], start_and_end[1:])
            ]
            slices
            
            ###############################################################################
            kernelizers_tuples = [(name, preprocess_pipeline, slice_)
                                  for name, slice_ in zip(feature_names, slices)]
            column_kernelizer = ColumnKernelizer(kernelizers_tuples)
            column_kernelizer
            
            # (Note that ``ColumnKernelizer`` has a parameter ``n_jobs`` to parallelize
            # each ``Kernelizer``, yet such parallelism does not work with GPU arrays.)
            
            ###############################################################################
            # Then we can define the model pipeline.
            pipe_1 = make_pipeline(column_kernelizer, model_1)

            # pipeline = make_pipeline(
            #     column_kernelizer,
            #     mkr_model,
            # )
            # pipeline
            # pipe_1 = make_pipeline(
            #     column_kernelizer,
            #     model_1,
            # )
            # pipeline
            ###############################################################################
            # Fit the model
            # -------------
            #
            # We fit on the train set, and score on the test set.
            #
            # To speed up the fit and to limit the memory peak in Colab, we only fit on
            # voxels with explainable variance above 0.1.
            #
            # With a GPU backend, the fitting of this model takes around 6 minutes. With a
            # CPU backend, it can last 10 times more.
            
            # pipeline.fit(X_train, Ytrain_cv)
            pipe_1.fit(X_train, Ytrain_cv)
            scores_rs = pipe_1.score(X_test, Ytest_cv)
            # scores = pipeline.score(X_test, Ytest_cv)
    
            
            
            scores_rs = backend.to_numpy(scores_rs)
            solver = "hyper_gradient"
            # solver_params = dict(max_iter=200, n_targets_batch=n_targets_batch, tol=1e-3,
            #          initial_deltas="ridgecv", max_iter_inner_hyper=1,
            #          hyper_gradient_method="direct")
            solver_params = dict(max_iter=100, hyper_gradient_method="direct",
                          max_iter_inner_hyper=5,
                          initial_deltas="here_will_go_the_previous_deltas", n_targets_batch=n_targets_batch, tol=1e-3)
    
            model_2 = MultipleKernelRidgeCV(kernels="precomputed", solver="hyper_gradient",
                                    solver_params=solver_params,cv=cv)
            pipe_2 = make_pipeline(column_kernelizer, model_2)
            # top = 100  # top 60%
            # best_cv_scores = backend.to_numpy(pipe_1[-1].cv_scores_.max(0))
            # mask = best_cv_scores > np.percentile(best_cv_scores, 100 - top)
            
            pipe_2[-1].solver_params['initial_deltas'] = pipe_1[-1].deltas_[:]
            pipe_2.fit(X_train, Ytrain_cv)
            scores = pipe_2.score(X_test, Ytest_cv)
            # scores = pipeline.score(X_test, Ytest_cv)
    
            
            
            scores = backend.to_numpy(scores)
            cv_scores.append(scores)
            Ytest_pred  = pipe_2.predict(X_test)
            tot_corr = correlation_score(Ytest_cv, Ytest_pred)
            tot_corr = backend.to_numpy(tot_corr)
            corr_tot.append(tot_corr)
            
            cv_score = backend.to_numpy(pipe_2[1].cv_scores_)
            
            # cv_score = backend.to_numpy(pipeline[1].cv_scores_)

            mean_cv_scores = np.mean(cv_score, axis=1)
            
            x_array = np.arange(1, len(mean_cv_scores) + 1)
            plt.plot(x_array, mean_cv_scores, '-o')
            plt.grid("on")
            plt.xlabel("Number of gradient iterations")
            plt.ylabel("L2 negative loss (higher is better)")
            plt.title("Convergence curve, averaged over targets")
            plt.show()
            # Then we extend the scores to all voxels, giving a score of zero to unfitted
            # voxels.
    
            Y_test_pred_split = pipe_2.predict(X_test, split=True)
            # Y_test_pred_split = pipeline.predict(X_test, split=True)
    
            split_scores = r2_score_split(Ytest_cv, Y_test_pred_split)
            split_scores = backend.to_numpy(split_scores)
            corr_s = correlation_score_split(Ytest_cv,Y_test_pred_split)
            corr_s = backend.to_numpy(corr_s)
            for kk, score in enumerate(split_scores):
                 plt.hist(score, np.linspace(0, np.max(split_scores),50), alpha=0.7,
                 label="kernel %s" % feature_names[kk])
            plt.title(r"%s Histogram of $R^2$ generalization score split between kernels" % s)
            plt.legend()
            plt.show()
            best_alphas=backend.to_numpy(pipe_2[-1].deltas_)
            best_alphas = 1. / np.sum(np.exp(best_alphas), axis=0)
            plot_alphas_diagnostic(best_alphas=best_alphas,
                       alphas=alphas)
            plt.show()
            cv_scores_split.append(split_scores)
            corr_scores_split.append(corr_s)
            
        out_s = s+"_results_"+resmodstr+".mat"
        output = os.path.join(resdir,out_s)
   
        scipy.io.savemat(output,{'r2_scores': cv_scores,'r2_scores_split': cv_scores_split,'corr_scores': corr_tot,'corr_scores_split': corr_scores_split})

                        