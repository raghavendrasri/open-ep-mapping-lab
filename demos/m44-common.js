// m44 · Error compounding in an agent's chain of steps, as in labs/python/epml/agent.py.
// MIT License. tests/test_m44_demos.py checks these functions against Python.

// eq-m44-chain: n independent steps that each succeed with probability p.
export function chainSuccess(p, n) {
  return Math.pow(p, n);
}

// eq-m44-check: a step succeeds first time, or fails, is caught (c) and the retry succeeds (pRetry).
export function checkedStep(p, c, pRetry = 1) {
  return p + (1 - p) * c * pRetry;
}

export function checkedChain(p, c, n, pRetry = 1) {
  return Math.pow(checkedStep(p, c, pRetry), n);
}

// eq-m44-escape: expected wrong outputs that get past a reviewer who catches a share r.
export function escapedErrors(nTasks, pTask, r) {
  return nTasks * (1 - pTask) * (1 - r);
}

// eq-m44-mixture: a share h of tasks is hard (step success pHard), the rest easy (pEasy).
export function mixtureChain(pEasy, pHard, h, n) {
  return (1 - h) * Math.pow(pEasy, n) + h * Math.pow(pHard, n);
}
