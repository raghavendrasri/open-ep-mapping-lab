% m05 lab (GNU Octave / MATLAB) · Time-frequency tools: spectra, the analytic signal and wavelets
%
% Open EP Mapping Lab. Education only: not for diagnosis, treatment or any clinical decision.
% MIT License. Runs in GNU Octave with core functions only (fft, filter; no signal package). It uses Octave's
% chained indexing f(x)(i); in MATLAB, replace it with temporary variables.
%
% This is the Octave copy of parts A-E of labs/python/m05_lab.ipynb. Run with:  octave-cli m05_lab.m
% Set the environment variable EPML_NO_PLOTS=1 to skip figures (CI does this).
% All signals are synthetic, in relative units.
% The "check" lines pass with the code as given; if one fails after a change, that is information.

make_plots = isempty(getenv('EPML_NO_PLOTS'));
check = @(cond, msg) assert(cond, msg);

hannw = @(n) 0.5 - 0.5 * cos(2 * pi * (0:n-1)' / n);                     % periodic Hann
% one-sided power spectrum (relative scale) on an nfft grid
pspec = @(x, w, nfft) abs(fft(x(:) .* w, nfft)(1:floor(nfft/2) + 1)).^2;
two_tone = @(fs, T, f1, f2, a2) cos(2*pi*f1*(0:round(fs*T)-1)'/fs) + a2 * cos(2*pi*f2*(0:round(fs*T)-1)'/fs + 0.3);
% analytic signal by the FFT (eq-m05-analytic)
analytic = @(x) ifft(fft(x(:)) .* [1; 2 * ones(floor((numel(x) - 1) / 2), 1); ones(mod(numel(x) + 1, 2), 1); zeros(floor((numel(x) - 1) / 2), 1)]);
turns = @(x) (unwrap(angle(analytic(x - mean(x))))(end) - unwrap(angle(analytic(x - mean(x))))(1)) / (2 * pi);

% ------------------------------------------------------------------ Part A
disp('Part A: frequency resolution');
fs = 200; res = zeros(1, 3); Ts = [0.5 1 2];
for k = 1:3
  x = two_tone(fs, Ts(k), 6, 7, 1); n = numel(x); nfft = 64 * n;
  P = pspec(x, ones(n, 1), nfft); f = (0:nfft/2)' * fs / nfft;
  band = f >= 6 & f <= 7;
  p6 = P(round(6 * nfft / fs) + 1); p7 = P(round(7 * nfft / fs) + 1);
  res(k) = min(P(band)) < 0.5 * min(p6, p7);
  fprintf('  T = %.1f s: %s\n', Ts(k), merge(res(k), 'two peaks', 'one peak'));
end
check(isequal(res, [0 1 1]), 'resolution is about 1/T'); disp('  check passed: resolution about 1/T');

% ------------------------------------------------------------------ Part B
disp('Part B: windows and leakage');
n = 256; pad = 64;
for name = {'rect', 'hann'}
  if strcmp(name{1}, 'rect'), w = ones(n, 1); else, w = hannw(n); end
  W = abs(fft(w, n * pad)); W = W(1:end/2) / max(W);
  i = 1; while W(i + 1) < W(i), i = i + 1; end
  sl = 20 * log10(max(W(i:end)));
  fprintf('  %s window: highest sidelobe %.1f dB, first null at %.0f bins\n', name{1}, sl, (i - 1) / pad);
  if strcmp(name{1}, 'rect'), check(abs(sl + 13.26) < 0.1, 'rectangular sidelobe'); else, check(abs(sl + 31.47) < 0.1, 'Hann sidelobe'); end
end
disp('  check passed: -13.3 dB and -31.5 dB');

% ------------------------------------------------------------------ Part C
disp('Part C: the variance of a spectrum');
randn('seed', 5); fs = 200; N = 1600; cv = zeros(1, 2); Ks = [1 8];
for q = 1:2
  K = Ks(q); vals = [];
  for trial = 1:200
    x = randn(N, 1); L = N / K; P = zeros(L/2 - 1, 1);
    for seg = 1:K
      S = abs(fft(x((seg-1)*L + 1:seg*L))).^2; P = P + S(2:L/2);
    end
    vals = [vals; P / K];
  end
  cv(q) = std(vals) / mean(vals);
  fprintf('  K = %d: std / mean = %.3f (1/sqrt(K) = %.3f)\n', K, cv(q), 1 / sqrt(K));
end
check(abs(cv(1) - 1) < 0.03 && abs(cv(2) * sqrt(8) - 1) < 0.05, 'Welch averaging divides the spread by sqrt(K)');
disp('  check passed: spread 1, and 1/sqrt(K) after averaging');

% ------------------------------------------------------------------ Part D
disp('Part D: pulse trains');
fs = 1000; cyc = 0.18; wdt = 0.004; t = (0:8*fs - 1)' / fs;
x = zeros(size(t));
for tk = cyc/2:cyc:8
  x = x - (t - tk) / wdt .* exp(-0.5 * ((t - tk) / wdt).^2);
end
nfft = 8 * numel(x); f = (0:nfft/2)' * fs / nfft;
P = pspec(x - mean(x), hannw(numel(x)), nfft);
band = f >= 2 & f <= 400; fb = f(band); [~, i] = max(P(band)); raw = fb(i);
% band-pass (second-order Butterworth high-pass 40 Hz and low-pass 250 Hz), rectify, low-pass 20 Hz, all zero-phase
Wp = @(fc) 2 * fs * tan(pi * fc / fs); K2 = 2 * fs;
den = @(fc) [K2^2 + sqrt(2)*Wp(fc)*K2 + Wp(fc)^2, 2*(Wp(fc)^2 - K2^2), K2^2 - sqrt(2)*Wp(fc)*K2 + Wp(fc)^2];
zp = @(b, a, v) flipud(filter(b, a, flipud(filter(b, a, v))));
y = zp(K2^2 * [1 -2 1], den(40), x); y = zp(Wp(250)^2 * [1 2 1], den(250), y);
y = abs(y); y = zp(Wp(20)^2 * [1 2 1], den(20), y);
P = pspec(y - mean(y), hannw(numel(y)), nfft);
band = f >= 3 & f <= 15; fb = f(band); [~, i] = max(P(band)); pre = fb(i);
fprintf('  1/T0 = %.2f Hz; raw peak %.2f Hz (harmonic %.1f); after preprocessing %.2f Hz\n', 1/cyc, raw, raw * cyc, pre);
check(round(raw * cyc) > 3 && abs(pre - 1/cyc) < 0.1, 'raw peak at a harmonic; preprocessed at the rate');
disp('  check passed: harmonic before, fundamental after preprocessing');

% ------------------------------------------------------------------ Part E
disp('Part E: the analytic signal and instantaneous phase');
t = (0:4*fs - 1)' / fs;
s = cos(2*pi*5*t);
fprintf('  sinusoid: %.2f turns for 20 periods\n', turns(s));
single = zeros(size(t)); dbl = zeros(size(t)); acts = 0;
for tk = 0.09:0.18:4
  single = single - (t - tk) / wdt .* exp(-0.5 * ((t - tk) / wdt).^2);
  dbl = dbl - 0.8 * (t - tk - 0.04) / wdt .* exp(-0.5 * ((t - tk - 0.04) / wdt).^2);
  acts = acts + 1;
end
dbl = dbl + single;
fprintf('  %d activations: one deflection %.1f turns, two deflections %.1f turns\n', acts, turns(single), turns(dbl));
check(abs(turns(s) - 20) < 0.02, 'one turn per period for a sinusoid');
check(abs(turns(single) - acts) < 0.5 && abs(turns(dbl) - 2 * acts) < 0.5, 'two deflections per cycle give two turns');
disp('  check passed: phase turns count deflections, not activations');
if make_plots
  figure; plot(t, unwrap(angle(analytic(dbl - mean(dbl)))) / (2*pi)); xlabel('time (s)'); ylabel('phase turns');
end
disp('All checks passed.');
