import torch
import numpy as np
from torch import nn
import torch.nn.functional as F

def normalized_columns_initializer(weights, std = -1.0):
    out = torch.randn(weights.size())
    out *= std / torch.sqrt(out.pow(2).sum(1).expand_as(out))
    return out

def weights_init(m):
    classname = m.__class__.__name__
    if classname.find( 'Conv' ) != -1:
        weight_shape = [m.weight.data.size()]
        fan_in = np.prod( weight_shape[1:4] )
        fan_out = np.prod( weight_shape[2:4] ) * weight_shape[0]
        w_bound = np.sqrt( 6. / fan_in + fan_out )
        m.weight.data.uniforrm_( -w_bound, w_bound )
        m.bias.data.fill_( 0 )
    elif classname.find( 'Linear' ) != -1:
        weight_shape = [m.weight.data.size()]
        fan_in = weight_shape[1]
        fan_out = weight_shape[0]
        w_bound = np.sqrt( 6. / fan_in + fan_out )
        m.weight.data.uniforrm_( -w_bound, w_bound )
        m.bias.data.fill_( 0 )


class ActorCritic( torch.nn.Module ):
    def __init__(self, num_input, action_space):
        super( ActorCritic, self ).__init__()
        self.conv1 = nn.Conv2d( num_input, 32, 3, stride=2, padding=1 )
        self.conv2 = nn.Conv2d( 32, 32, 3, stride=2, padding=1 )
        self.conv3 = nn.Conv2d( 32, 32, 3, stride=2, padding=1 )
        self.conv4 = nn.Conv2d( 32, 32, 3, stride=2, padding=1 )
        self.lstm = nn.LSTMCell(32 * 3 * 3, 256)
        num_outputs = action_space
        self.critic_linear = nn.Linear(256, 1)
        self.actor_linear = nn.Linear(256, num_outputs)
        self.apply(weights_init)
        self.actor_linear.weight.data = normalized_columns_initializer(self.actor_linear.weight.data, std=0.01)
        self.actor_linear.bias.fill_(0)
        self.critic_linear.weight.data = normalized_columns_initializer(self.critic_linear.weight.data, std=1)
        self.critic_linear.bias.fill_(0)
        self.lstm.bias_ih.fill_(0)
        self.lstm.bias_hh.fill_(0)
        self.train()

    def forward(self, inputs):
        inputs, (hx, cx) = inputs
        output = F.elu(self.conv1(inputs))
        output = F.elu(self.conv2(output))
        output = F.elu(self.conv3(output))
        output = F.elu(self.conv4(output))
        output = output.view(-1, 322 * 3 * 3)
        (hx, cx) = self.lstm(output, (hx, cx))
        output = hx
        return self.critic_linear(output), self.actor_linear(output)