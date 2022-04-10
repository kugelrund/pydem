import numpy
import scipy.interpolate
import scipy.optimize
import scipy.sparse.linalg


def smooth_old(x, y):
    assert len(x) == len(y)
    n = len(x)
    rows = []
    cols = []
    vals = []
    b = numpy.zeros((n-2,1))
    for i in range(0, n-2):
        if i > 0:
            rows.append(i)
            cols.append(i-1)
            vals.append(y[i+1] - y[i])
        rows.append(i)
        cols.append(i)
        vals.append(-(y[i+2] - y[i]))
        b[i] = (y[i+2] - y[i]) * x[i+1] - (y[i+2] - y[i+1]) * x[i] - (y[i+1] - y[i]) * x[i+2]
        if i < n-3:
            rows.append(i)
            cols.append(i+1)
            vals.append(y[i-1] - y[i])
    A = scipy.sparse.coo_matrix((vals, (rows, cols)))
    deltax = scipy.sparse.linalg.lsqr(A, b, damp=n/10000)[0]
    deltax = numpy.concatenate(([0.0], deltax, [0.0]))

    #assert numpy.all((x+deltax)[:-1] <= (x+deltax)[1:])

    return numpy.interp(x, x + deltax, y)


def smooth(x, y):
    x = numpy.array(x)
    y = numpy.array(y)
    assert len(x) == len(y)
    n = len(x)

    rows = []
    cols = []
    vals = []
    b = []
    i_row = 0

    for r, s in zip([1,2,3,4], [1.0, 0.5, 0.25, 0.125]):
        for i in range(r, n-r):
            rows.append(i_row)
            cols.append(i-r)
            vals.append(-(y[i+r] - y[i]) * s)
            rows.append(i_row)
            cols.append(i)
            vals.append((y[i+r] - y[i-r]) * s)
            rows.append(i_row)
            cols.append(i+r)
            vals.append(-(y[i] - y[i-r]) * s)
            b.append(((y[i+r] - y[i]) * x[i-r] - (y[i+r] - y[i-r]) * x[i] + (y[i] - y[i-r]) * x[i+r]) * s)
            i_row += 1

    A = scipy.sparse.coo_matrix((vals, (rows, cols)))
    b = numpy.array(b)

    damp = 0.5 * numpy.std(y)
    objective_matrix = lambda deltax: 1/n * (sum((A @ deltax - b) ** 2) + damp * sum(deltax ** 2))
    objective = lambda deltax: 1/n * (sum((-(y[2:] - y[:-2]) * (x[1:-1] + deltax[1:-1])
                                           +(y[2:] - y[1:-1]) * (x[:-2] + deltax[:-2])
                                           +(y[1:-1] - y[:-2]) * (x[2:] + deltax[2:])) ** 2) + damp * sum(deltax ** 2))
    objective = objective_matrix
    test = numpy.random.randn(n)
    assert abs(objective_matrix(test) - objective(test)) < 1e-6

    gradient_matrix = lambda deltax: 1/n * (2 * A.T @ (A @ deltax - b) + damp * 2 * deltax)
    gradient = lambda deltax: 1/n * (2 * (
        numpy.concatenate(([0.0], (-(y[2:] - y[:-2]) * (x[1:-1] + deltax[1:-1])
                                   +(y[2:] - y[1:-1]) * (x[:-2] + deltax[:-2])
                                   +(y[1:-1] - y[:-2]) * (x[2:] + deltax[2:])) * (y[:-2] - y[2:]), [0.0])) +
        numpy.concatenate(([0.0, 0.0], (-(y[2:] - y[:-2]) * (x[1:-1] + deltax[1:-1])
                                        +(y[2:] - y[1:-1]) * (x[:-2] + deltax[:-2])
                                        +(y[1:-1] - y[:-2]) * (x[2:] + deltax[2:])) * (y[1:-1] - y[:-2]))) +
        numpy.concatenate(((-(y[2:] - y[:-2]) * (x[1:-1] + deltax[1:-1])
                            +(y[2:] - y[1:-1]) * (x[:-2] + deltax[:-2])
                            +(y[1:-1] - y[:-2]) * (x[2:] + deltax[2:])) * (y[2:] - y[1:-1]), [0.0], [0.0])))
        + damp * 2 * deltax)
    gradient = gradient_matrix
    test = numpy.random.randn(n)
    assert numpy.linalg.norm(gradient_matrix(test) - gradient(test)) < 1e-6

    hessian = lambda deltax: 1/n * (2 * A.T @ A + damp * 2 * scipy.sparse.eye(n))

    x0 = numpy.zeros(n)

    rows = []
    cols = []
    vals = []
    for i in range(0, n-1):
        rows.append(i)
        cols.append(i)
        vals.append(1.0)
        rows.append(i)
        cols.append(i+1)
        vals.append(-1.0)
    constraints = scipy.optimize.LinearConstraint(
        scipy.sparse.coo_matrix((vals, (rows, cols))),
        lb=-numpy.inf, ub=x[1:] - x[:-1])
    lb = -numpy.inf * numpy.ones(n)
    ub = numpy.inf * numpy.ones(n)
    lb[0] = 0.0
    ub[-1] = 0.0
    #for i in range(0, n-1):
    #    ub[i] = (x[i+1] - x[i]) / 2
    #for i in range(1, n):
    #    lb[i] = (x[i-1] - x[i]) / 2
    bounds = scipy.optimize.Bounds(lb, ub)
    res = scipy.optimize.minimize(objective, x0, jac=gradient, hess=hessian, constraints=constraints, bounds=bounds, method='trust-constr',
        options={'disp': True, 'verbose': 2, 'maxiter': 5000})
    deltax = res.x

    assert numpy.all((x+deltax)[:-1] - (x+deltax)[1:] <= 1e-14)
    return numpy.interp(x, x + deltax, y)
