<<hero>>

A periodic box holds a grid of counter-rotating vortices. In a viscous fluid the pattern keeps its shape
and only fades, all velocities shrinking by the same factor, so the Navier–Stokes equations have a closed-form
solution for it. That makes the Taylor–Green vortex the one flow where the dissipation of an SPH scheme can be
measured instead of assumed. This page runs it with five schemes of warpSPH, weakly compressible and
incompressible side by side, and compares each with the exact solution.

<<colab>>

## Origin and purpose

The vortex was introduced by Taylor and Green in their study of how large eddies break up into small ones
{% cite taylor1937 --file cases %}. The initial field is smooth, divergence free and has no boundaries, so it
isolates the scheme: any deviation from the exact decay is dissipation, lattice noise or volume error of the
discretisation, not of a wall treatment.

It is a standard benchmark for weakly compressible SPH {% cite sun2019 --file cases %} and has been used to
cross-validate SPH-based learned models {% cite winchenbach2024pmac --file cases %}.

What it tests:

- **Dissipation.** The kinetic energy must decay at the rate the viscosity prescribes. The fitted effective
  viscosity divided by the prescribed one (`nu_eff/nu` below) is 1 for a scheme that dissipates exactly what
  it was asked to.
- **Accuracy of the velocity field.** The exact field is known at every particle, so the error is a pointwise
  L2 norm, not just an integral quantity.
- **Volume error.** The flow is incompressible, so a weakly compressible scheme must keep the density close to
  its rest value and an incompressible one must hold it; the spread of the particle density shows how well.
- **Particle disorder.** Lattice noise and clumping show up as velocity error well before they show up in the
  energy.

## Setup

The box is `[0, 2π]²` with periodic boundaries. With wavenumber `k = 1` the velocity is

`v = U e^(-2 ν k² t) ( cos(kx + φ) sin(ky + φ), -sin(kx + φ) cos(ky + φ) )`,

with `φ = π/2`, and the kinetic energy decays as `E(t) = E(0) e^(-4 ν k² t)`, `E(0) = ρ₀ U² L² / 4`. The same
solution gives the exact velocity of every particle at every time; the particles move, and the field is evaluated
at their current positions.

| quantity | weakly compressible (`tgv-wc`) | incompressible (`tgv`) |
|---|---|---|
| schemes | `deltaSPH`, `sun2017DeltaSPH`, `artificialCompressible` | `divergenceFree`, `omniIncompressible` |
| velocity scale `U`, rest density `ρ₀` | 1, 1 | 1, 1 |
| kinematic viscosity `ν` | 0.01 | 0.01 |
| Reynolds number `U L / (2ν)` | 314 | 314 |
| resolution `nx` (particles per direction) | 128 | 128 |
| kernel | Wendland C4 | Wendland C2 |
| time integration | Runge–Kutta 2, adaptive step | semi-implicit Euler, adaptive step |
| initial particle arrangement | regular lattice, 128 shuffle iterations | regular lattice relaxed for 32 steps |
| end time | 2 | 2 |
| precision | float32 | float32 |

The two groups use the two registered cases of the same flow, which differ in how they arrange the initial
particles; the physical problem is identical. `artificialCompressible` is registered under `tgv-wc` and is a
scheme for incompressible flow, so it sits in the weakly compressible column only because of the case it is run
through.

Run the headline configurations with

<<command:deltaSPH__default__nx128>>

<<command:divergenceFree__default__nx128>>

The schemes: `deltaSPH` is the δ-SPH step {% cite marrone2011 --file cases %} with the scheme's default particle
shifting; `sun2017DeltaSPH` is the same step with the prescription of the δ⁺-SPH paper
{% cite sun2017 --file cases %} (diffusion frozen across the Runge–Kutta stages and that paper's shifting constants).
`artificialCompressible` is the incompressible δ-SPH of De Courcy et al. {% cite decourcy2024 --file cases %};
`omniIncompressible` is a port of the omniSPH incompressible loop; and `divergenceFree` is warpSPH's divergence-free
projection step.

## Results

<<figure:energy>>

<<figure:maps>>

## Solver comparison

<<table:comparison>>

`L2 v` is the root-mean-square velocity error over all particles at the end time, relative to the exact
amplitude at that time. `KE error` is the relative deviation of the kinetic energy at the end time from the exact
value. `nu_eff/nu` is the viscosity that reproduces the measured energy decay (least-squares fit of the logarithm
of the energy over the whole run), divided by the prescribed one.

<<figure:density>>

## Reference comparison

All numbers above are against the exact solution given in *Setup*; there is no digitised or converged reference
involved. The table gives the error at each resolution and the observed order between consecutive resolutions (negative when the
error grows).

<<figure:convergence>>

<<table:orders>>

## Known limitations

- **The velocity error stops decreasing at the finest resolution** for most schemes (the table shows an order near
  zero or negative between the last two resolutions; the figure's legend says where it stops). Single-precision
  round-off and, for the weakly compressible schemes, the compressibility error at a fixed sound speed set a floor
  that a finer lattice does not lower; no convergence order is claimed beyond that point.
- The weakly compressible schemes and the incompressible ones start from different particle arrangements, so
  part of what separates the two groups is the initial lattice noise rather than the scheme.
- A single Reynolds number is shown here.
- All runs are float32 on a single GPU; the golden trajectories are compared with tolerances, not bit for bit.

## Reproduce

<<reproduce>>

## References

<<refs>>
