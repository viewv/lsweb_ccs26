# Adaptive Sampling Assistant

An interactive command-line tool implementing the adaptive probability
sampling strategy proposed in the paper (Section 8, Practical Guidance for
Sampling). Researchers who must estimate the affected-unit rate of an issue
without knowing its prevalence can use this assistant to decide, stage by
stage, whether the current sample is sufficient or whether more units must
be measured.

## The stopping rule

1. Declare the target population (frame) of size `N` and a relative
   tolerance `tau` (default 0.05).
2. Draw a 2% pilot. The pilot cannot stop: stability requires comparing two
   consecutive estimates.
3. At every later stage with cumulative sample size `n` and `x` affected
   units, the assistant computes:
   - `p = x / n`
   - `D = |p_current - p_previous| / p_current`  (relative change)
   - `R = h / p`, where `h` is the half-width of an approximate 95%
     proportion interval with finite-population correction
4. Stop only when `x > 0` AND `D <= tau` AND `R <= tau`; otherwise double
   the cumulative sample, with `N` as the predeclared maximum.

## Usage

Only the Python standard library is required (no numpy/pandas).

```bash
# Interactive mode (guided, stage by stage)
python3 adaptive_sampling_assistant.py \
    --frame-size 500000 --tau 0.05 --confidence 95

# Custom enlargement schedule
python3 adaptive_sampling_assistant.py \
    --frame-size 100000 --tau 0.05 \
    --stages 2000,4000,8000,16000,32000,64000,100000

# Batch / scripted evaluation of an explicit (n, x) sequence
python3 adaptive_sampling_assistant.py \
    --frame-size 100000 --tau 0.05 \
    --batch 4000,934 8000,1867 16000,3734
```

In interactive mode, enter the observed number of affected units `x` at each
stage; the assistant prints the estimate, both stopping statistics, the
decision, and how many additional units to collect next. Type `q` to quit.

In batch mode, each `n,x` pair is one stage; the assistant prints a
STOP/CONTINUE verdict for each stage and exits at the first stop.

## Worked example (matches the paper's case study)

Tranco Top-100K, Cookie security (true rate ~23.3%), `tau=0.05`:

```text
stage 1: n= 4,000 x=  934 p= 23.35%  D=   n/a  R=0.055  => CONTINUE
stage 2: n= 8,000 x=1,867 p= 23.34%  D=0.0005  R=0.038  => STOP
```

The 4% sample is not yet precise enough (relative half-width 0.055 > 0.05);
at 8% both conditions hold, matching the median stopping fraction reported
for Cookie security in the paper's case-study table.

## Notes

- The rule is a *stopping* procedure, not a claim of sequentially
  simultaneous 95% coverage; the interval is a familiar margin-of-error
  diagnostic.
- Predeclare `N`, `tau`, and the enlargement schedule before measuring.
- Report the final `n`, `x`, `p`, and interval half-width alongside the
  estimate.
