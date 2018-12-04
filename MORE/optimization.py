import numpy as np
from scipy.optimize import minimize


'''
    Use: https://en.wikipedia.org/wiki/Sequential_quadratic_programming
         method="SLSQP" https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html

    Variables have to be in numpy
    We need to pass a starting point, I suggest x = (1,1) (could be discussed with Boris)

    # TODO: weitere Nebenbedingung etha, omega > 0
'''

class OPTIMIZATION(object):
    def __init__(self, Q, b, R, r, epsilon, gamma):
        self.Q = Q # .detach().numpy()
        self.b = b # .detach().numpy()
        self.R = R # .detach().numpy()
        self.r = r # .detach().numpy()
        self.epsilon = epsilon
        self.beta = self.compute_beta(gamma, Q)

    '''
        Our function g, which we want to minimize
        Param x: contains the langragian parameter etha and omega
    '''
    def objective(self, x):
        etha = x[0]
        omega = x[1]

        # Transform arrays into col-vectors
        self.b = self.b.reshape(self.b.size, 1)
        self.r = self.r.reshape(self.r.size, 1)

        F = etha * np.linalg.inv(self.Q) - 2 * np.linalg.inv(self.R)
        f = etha *  np.linalg.inv(self.Q) @ self.b + self.r

        # Our objective Function g, see Chapter 2.2
        g = etha * self.epsilon - self.beta * omega + .5 * (f.T @ F @ f \
                - etha * self.b.T @  np.linalg.inv(self.Q) @ self.b \
                - etha * np.log(2 * np.pi *  np.linalg.det(self.Q)) \
                + (etha + omega) * np.log(np.linalg.det(2 * np.pi * (etha + omega) * F)))

        return g[0,0]

    '''
        F needs to be positive definite (det(F) > 0)
    '''
    def constraint(self, x):
        etha = x[0]
        F = np.linalg.det(etha * np.linalg.inv(self.Q) - 2 *  np.linalg.inv(self.R)) - 1e-10
        return F

    '''
        Constraint übergeben?
    '''
    def SLSQP(self, x0):
        cons = {'type': 'ineq', 'fun': self.constraint}
        soloution = minimize(self.objective, x0, method = 'SLSQP',constraints = cons)
        return soloution

    '''
        Updates our mu and dev for the sampling method
    '''
    def update_pi(self, F, f, etha, omega):
        return F @ f, F * (etha + omega)

    '''
        Bishop PDF page 69 Formel (1.93)
        H[pi0] = -75
        q = actual probability distribution

        we use: https://en.wikipedia.org/wiki/Multivariate_normal_distribution#Entropy
    '''
    def compute_beta(self, gamma, Q):
        k = Q.shape[0]
        H_q = (k/2) + (k * np.log(2 * np.pi)) / 2 + np.log(np.linalg.det(Q)) / 2
        H_pi0 = -75
        beta = gamma * (H_q - H_pi0) + H_pi0

        return beta
