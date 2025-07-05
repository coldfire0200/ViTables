import numpy
import scipy

def rf_to_gray(rf_input, dyanmic_range):
    env = numpy.abs(scipy.signal.hilbert(rf_input))
    log_comp = 20 * numpy.log10(env)
    if len(log_comp) == 2:
        log_comp = numpy.expand_dims(log_comp, axis=0)
    for frame in range(log_comp.shape[0]):
        max_val = numpy.max(log_comp[frame,:])
        log_comp[frame,:] -= max_val
    log_comp = numpy.clip(log_comp, -dyanmic_range, 0)
    return log_comp