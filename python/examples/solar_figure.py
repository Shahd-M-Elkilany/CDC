# %% [markdown]
# # Solar constant in the SNR model (Step 1)
# EGS YZH MAN 129 00. The absolute value E_SC = 1400 W/m² comes from §5.2 stage 4 (p. 13) and
# Annex B p. 22. The spectral table, λ and W(λ), is on Annex B p. 23.
#
# In VS Code, click **Run Cell** above each `# %%`, or press Shift+Enter. The figure appears
# in the Interactive window beside the code. Running the file normally works too:
# `python examples/solar_figure.py` opens it in a window.

# %% The two arrays from Annex B p. 23 and the solar constant
import matplotlib.pyplot as plt

from cdc.snr import SNRInputs, calculate
from cdc.snr.model import E_SC, SOLAR_LAMBDA, SOLAR_W, in_band_solar_constant
from cdc.snr.plots import plot_solar

print(f"E_SC = {E_SC:g} W/m²   ({len(SOLAR_LAMBDA)} table points, "
      f"λ = {SOLAR_LAMBDA[0]*1e6:g}…{SOLAR_LAMBDA[-1]*1e6:g} µm)")
for lam, w in zip(SOLAR_LAMBDA, SOLAR_W, strict=True):
    print(f"  λ = {lam*1e6:5.2f} µm   W = {w:.4f}")

# %% Inputs - change any of the 27 (names: python -m cdc snr --list-inputs)
p = SNRInputs(lam_min=0.5e-6, lam_max=0.885e-6, sun_elevation=30)
r = calculate(p)
e_band = in_band_solar_constant(p.lam_min, p.lam_max)
print(f"W(λmin) = {r.W_min:.4f}   W(λmax) = {r.W_max:.4f}")
print(f"in band: {E_SC:g} × ({r.W_max:.4f} − {r.W_min:.4f}) = {e_band:.3f} W/m²")
print(f"→ stage 4: E_Edir = {r.E_Edir:.3f} W/m²")
print(f"µL = {r.mu_L:.4f}   µD = {r.mu_D:.4f}   µx = {r.mu_x:.4f}   µy = {r.mu_y:.4f}")

# %% The figure
plot_solar(p, fig=plt.figure(num="Solar constant in the SNR model"))
plt.show()
