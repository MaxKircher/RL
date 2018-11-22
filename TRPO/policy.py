import torch
import numpy as np
from scipy.stats import norm

class NN(object):

    '''
        The last theta parameters (exactly the last action_space.dim) are for standard deviation
    '''
    def __init__(self, s_dim, a_dim):
        self.s_dim = s_dim
        self.a_dim = a_dim

        inter_dim = 10
        self.model = torch.nn.Sequential( # neuronale Netzwerk
            torch.nn.Linear(self.s_dim, inter_dim), #Applies a linear transformation to the incoming data
            # inter_dim Knoten im intermediate layer
            torch.nn.ReLU(), # Activation functeion, see rectified linear unit
            torch.nn.Linear(inter_dim, self.a_dim),
        )

        # Is a parameter and not a tensor ?! maybe update the following line!
        self.model.log_dev = torch.nn.Parameter(torch.ones(self.a_dim, requires_grad=True)) #see https://pytorch.org/docs/stable/notes/autograd.html


        # choose action
    def choose_a(self, s):
        mu = self.model(torch.tensor(s)).detach().numpy() # Vektor für den action space
        dev = np.exp(self.model.log_dev.detach().numpy()) # deviation
        return np.random.normal(mu, dev, 1)

    # pi_theta old
    def q(self, s, a):
        mu = self.model(torch.tensor(s, dtype = torch.float)).detach().numpy() # Vektor für den action space
        dev = np.exp(self.model.log_dev.detach().numpy()) # deviation

        return norm.pdf(a, mu, dev) # ist auch multivariat

    # quasi pi_theta neu
    # von pytorch ausgerechnetete Wahrscheinlichkeit die man ableiten kann
    def pi_theta(self, s, a): #liefert das gleiche zurück wie q nur für torch interpretierbar, sodass diese Funktion optmiert werden kann
        mu = self.model(torch.tensor(s, dtype = torch.float)).double()
        dev = torch.exp(self.model.log_dev).double()
        covariance_matrix = dev * torch.eye(dev.shape[0]).double()
        # factor = 1/(torch.tensor(np.sqrt(2*np.pi))*dev)
        # exponent = -(torch.tensor(a).double()-mu.double()).pow(2)/(2*(dev.double().pow(2)))
        # return  factor*torch.exp(exponent)

        # aufstellen normal_distribution
        normal_distribution = torch.distributions.multivariate_normal.MultivariateNormal(mu, covariance_matrix)
        return torch.exp(normal_distribution.log_prob(torch.tensor(a).double()))

    '''
        DONE UPDATE MU with stdev

        Updates the parameter of the policy improve our policy
        Parameter:
         - theta_new: is ideally of the form nn.Parameters otherwise if it's a tensor
                      do nn.Parameters(theta_new)
    '''
    def update_policy_parameter(self, theta_new):

        theta_new = theta_new.view(-1) # we had [1, 73] but 1 was nonsense
        # print(theta_new.size())

        # split parameter for the desired model
        number_of_layers = len(self.model)
        j = 0 # get right position where we get the params from theta_new
        for i in range(number_of_layers):

            if type(self.model[i]) == torch.nn.modules.linear.Linear:
                size_weight = self.model[i].weight.size()
                size_bias = self.model[i].bias.size()

                no_weights = self.model[i].weight.nelement()
                no_bias = self.model[i].bias.nelement()
                # get the new weights
                theta_new_weights = theta_new[j: j + no_weights]
                j += no_weights
                theta_new_bias = theta_new[j: j + no_bias]
                j += no_bias

                self.model[i].weight.data = theta_new_weights.view(size_weight)
                self.model[i].bias.data = theta_new_bias.view(size_bias)

        # keine negativen Varianzen
        # print(torch.max(torch.zeros(self.model.log_dev.size()),theta_new[j:]))
        self.model.log_dev.data = theta_new[j:] # update policy parameter

        # new_nn_params = torch.nn.Parameters(theta_new)
