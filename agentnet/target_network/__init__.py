"""
Implements the target network techniques in deep reinforcement learning.
In short, the idea is to estimate reference Qvalues not from the current agent state, but
from an earlier snapshot of weights. This is done to decorrelate target and predicted Qvalues/state_values
and increase stability of learning algorithm.

Some notable alterations of this technique:
- Standard approach with older NN snapshot
  - https://www.cs.toronto.edu/~vmnih/docs/dqn.pdf
- Moving average of weights
  - http://arxiv.org/abs/1509.02971
- Double Q-learning and other clever ways of training with target network
  - http://arxiv.org/pdf/1509.06461.pdf

Here we implement a generic TargetNetwork class that supports both standard and moving
average approaches through "moving_average_alpha" parameter of "load_weights".
"""

from ..utils.clone import clone_network
import lasagne
import theano.tensor as T
import theano
from collections import OrderedDict

class TargetNetwork(object):
    """
    A generic class for target network techniques.
    Works by creating a deep copy of the original network and synchronizing weights through
    "load_weights" method.

    :param original_network_outputs: original network outputs to be cloned for target network
    :type original_network_outputs: lasagne.layers.Layer or a list/tuple of such
    :param bottom_layers: the layers that should be shared between networks.
    :type bottom_layers: lasagne.layers.Layer or a list/tuple/dict of such.
    :param share_inputs: if True, all InputLayers will still be shared even if not mentioned in bottom_layers
    :type share_inputs: bool
    """
    #TODO(jheuristic) code snippet, auto names
    def __init__(self,original_network_outputs,bottom_layers=(),share_inputs=True):
        self.output_layers = clone_network(original_network_outputs,bottom_layers,share_inputs=share_inputs)
        self.original_network_outputs = original_network_outputs
        self.bottom_layers = bottom_layers

        #get all weights that are not shared between networks
        all_clone_params = lasagne.layers.get_all_params(original_network_outputs)
        all_original_params = lasagne.layers.get_all_params(original_network_outputs)

        #a dictionary {clone param -> original param}
        self.param_dict = {clone_param : original_param
                           for clone_param, original_param in zip(all_clone_params,all_original_params)
                           if clone_param != original_param}

        self.load_weights_hard = theano.function([],updates=self.param_dict)

        self.alpha = alpha = T.scalar('moving average alpha',dtype=theano.config.floatX)
        self.param_updates_with_alpha = OrderedDict({ clone_param:  (1-alpha)*clone_param + (alpha)*original_param
                                                     for clone_param,original_param in self.param_dict.items()
                                                    })
        self.load_weights_moving_average = theano.function([alpha],updates=self.param_updates_with_alpha)



    def load_weights(self,moving_average_alpha=1):
        """
        Loads the weights from original network into target network. Should usually be called whenever
        you want to synchronize the target network with the one you train.

        When using moving average approach, one should specify which fraction of new weights is loaded through
        moving_average_alpha param (e.g. moving_average_alpha=0.1)

        :param moving_average_alpha: If 1, just loads the new weights.
            Otherwise target_weights = alpha*original_weights + (1-alpha)*target_weights
        """
        assert 0<=moving_average_alpha<=1

        if moving_average_alpha == 1:
            self.load_weights_hard()
        else:
            self.load_weights_moving_average(moving_average_alpha)
