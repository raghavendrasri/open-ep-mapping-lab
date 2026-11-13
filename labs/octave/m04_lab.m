% m04 lab (GNU Octave / MATLAB) · Sampling, filtering and the EP recording chain
%
% Open EP Mapping Lab. Education only: not for diagnosis, treatment or any clinical decision.
% MIT License. Runs in GNU Octave with core functions only (filter; no signal package). It uses Octave's merge
% and chained indexing f(x)(i); in MATLAB, replace those with temporary variables.
%
% This is the Octave copy of parts A-E of labs/python/m04_lab.ipynb. Run with:  octave-cli m04_lab.m
% Set the environment variable EPML_NO_PLOTS=1 to skip figures (CI does this).
%
% Filter bands from Delacretaz et al. 2001 (unipolar 0.5-500 Hz, high-pass unipolar 100 Hz, bipolar 30-500 Hz).
% The test signal is the m03 unipolar model in relative units.
% The "check" lines pass with the code as given; if one fails after a change, that is information.

make_plots = isempty(getenv('EPML_NO_PLOTS'));
check = @(cond, msg) assert(cond, msg);

alias_f = @(f, fs) abs(f - fs * round(f / fs));                                   % eq-m04-sampling
egm = @(t, c) (-c * t) ./ ((c * t).^2 + 1.3^2);                                    % m03 unipolar, w + h = 1.3 mm
% second-order Butterworth by the bilinear transform with prewarping (eq-m04-butterworth)
Wp = @(fc, fs) 2 * fs * tan(pi * fc / fs);
a2 = @(fc, fs) [ (2*fs)^2 + sqrt(2)*Wp(fc,fs)*2*fs + Wp(fc,fs)^2, 2*(Wp(fc,fs)^2 - (2*fs)^2), (2*fs)^2 - sqrt(2)*Wp(fc,fs)*2*fs + Wp(fc,fs)^2 ];
lp2 = @(fc, fs) deal(Wp(fc,fs)^2 * [1 2 1] / a2(fc,fs)(1), a2(fc,fs) / a2(fc,fs)(1));
hp2 = @(fc, fs) deal((2*fs)^2 * [1 -2 1] / a2(fc,fs)(1), a2(fc,fs) / a2(fc,fs)(1));
zerophase = @(b, a, x) flipud(filter(b, a, flipud(filter(b, a, x(:)))));

% ------------------------------------------------------------------ Part A
disp('Part A: sampling');
fs = 1000; n = (0:99)';
fa = alias_f(850, fs);
same = max(abs(cos(2*pi*850*n/fs) - cos(2*pi*fa*n/fs))) < 1e-9;
fprintf('  850 Hz sampled at 1 kHz looks like %d Hz\n', fa);
check(same && fa == 150, 'aliasing'); disp('  check passed: aliasing');
rand('seed', 4);
er = zeros(400, 1); ef = zeros(400, 1);
t = (-50:1:49)';
for k = 1:400
  t0 = rand() - 0.5;
  x = egm(t - t0, 0.5);
  d = gradient(x, t);
  [~, i] = min(d);
  er(k) = t(i) - t0;
  off = 0.5 * (d(i-1) - d(i+1)) / (d(i-1) - 2*d(i) + d(i+1));
  ef(k) = t(i) + off - t0;
end
fprintf('  timing error at 1 kHz: nearest sample sd %.3f ms, refined sd %.3f ms\n', std(er), std(ef));
check(abs(std(er) - 1/sqrt(12)) < 0.05 && std(ef) < 0.5 * std(er), 'sampling limits timing; interpolation helps');
disp('  check passed: timing error about 1/sqrt(12) of a sample, reduced by refinement');

% ------------------------------------------------------------------ Part B
disp('Part B: quantization');
t = (0:199999)'; x = 0.98 * sin(2*pi*0.01234567*t);
for bits = [10 12 14]
  lsb = 2 / 2^bits;
  xq = max(min(round(x / lsb), 2^(bits-1) - 1), -2^(bits-1)) * lsb;
  snr = 10 * log10(mean(x.^2) / mean((xq - x).^2));
  formula = 20 * log10(2^bits * sqrt(1.5)) + 20 * log10(0.98);
  fprintf('  %d bits: SNR %.2f dB (formula %.2f dB)\n', bits, snr, formula);
  check(abs(snr - formula) < 0.1 && abs(std(xq - x) / (lsb / sqrt(12)) - 1) < 0.02, '6.02 N + 1.76 dB');
end
disp('  check passed: 6.02 N + 1.76 dB');

% ------------------------------------------------------------------ Part C
disp('Part C: filters by hand');
H = (1i) / (1 + 1i);                    % RC high-pass at f = fc (eq-m04-highpass)
fprintf('  RC high-pass at fc: |H| = %.4f, phase %.1f degrees\n', abs(H), angle(H) * 180 / pi);
check(abs(abs(H) - 1/sqrt(2)) < 1e-12 && abs(angle(H) * 180/pi - 45) < 1e-9, 'RC high-pass at fc');
[b, a] = lp2(30, 1000);
w = 2 * pi * 30 / 1000; z = exp(1i * w);
Hd = polyval(fliplr(b), 1/z) / polyval(fliplr(a), 1/z);
fprintf('  digital second-order Butterworth low-pass at 30 Hz: |H(fc)| = %.4f\n', abs(Hd));
check(abs(abs(Hd) - 1/sqrt(2)) < 1e-9, 'the prewarped bilinear transform keeps -3 dB at fc'); disp('  check passed: -3 dB at fc');

% ------------------------------------------------------------------ Part D
disp('Part D: filtering a unipolar electrogram');
fs = 20000; t = (-100:1000/fs:100 - 1000/fs)'; x = egm(t, 1);
bands = [0.5 500; 30 500; 100 0];
lat = zeros(3, 2); ratio = zeros(3, 2);
for q = 1:3
  for zp = 0:1
    y = x;
    [b, a] = hp2(bands(q, 1), fs);
    if zp, y = zerophase(b, a, y); else, y = filter(b, a, y); end
    if bands(q, 2) > 0
      [b, a] = lp2(bands(q, 2), fs);
      if zp, y = zerophase(b, a, y); else, y = filter(b, a, y); end
    end
    d = gradient(y, t); [~, i] = min(d);
    off = 0.5 * (d(i-1) - d(i+1)) / (d(i-1) - 2*d(i) + d(i+1));
    lat(q, zp+1) = t(i) + off * (t(2) - t(1));
    win = abs(t) < 20;
    ratio(q, zp+1) = (max(y(win)) - min(y(win))) / (max(x(win)) - min(x(win)));
    fprintf('  band %5.1f-%3d Hz, %s: downstroke at %+.3f ms, peak-to-peak x%.2f\n', bands(q,1), bands(q,2), ...
            merge(zp, 'zero-phase', 'causal    '), lat(q, zp+1), ratio(q, zp+1));
  end
end
check(all(abs(lat(:, 2)) < 0.02), 'zero-phase filtering keeps the activation time');
check(abs(lat(3, 1)) > 0.1, 'a causal 100 Hz high-pass moves it');
disp('  check passed: zero phase keeps timing; causal filters move it');
tb = (-0.2:1/fs:0.2 - 1/fs)'; bump = exp(-(tb / 0.01).^2);
[b, a] = lp2(100, fs); yb = filter(b, a, bump);
[~, i1] = max(yb); [~, i0] = max(bump);
shift = tb(i1) - tb(i0);
fprintf('  second-order 100 Hz low-pass delays a 10-ms bump by %.2f ms (formula %.2f ms)\n', 1000 * shift, 1000 * sqrt(2) / (2*pi*100));
check(abs(shift / (sqrt(2) / (2*pi*100)) - 1) < 0.1, 'group delay sqrt(2) / (2 pi fc)'); disp('  check passed: group delay');

% ------------------------------------------------------------------ Part E
disp('Part E: mains interference and the notch');
fs = 1000; t = (-3000:1:2999)';
clean = egm(t, 0.5); noisy = clean + 0.2 * sin(2*pi*50*t/1000);
w0 = 2*pi*50/fs; bw = w0 / 30; beta = tan(bw/2); g = 1 / (1 + beta);      % eq-m04-notch, as scipy iirnotch
b = g * [1, -2*cos(w0), 1]; a = [1, -2*g*cos(w0), 2*g - 1];
cleaned = zerophase(b, a, noisy);
mid = abs(t) < 300;
rb = std(noisy(mid) - clean(mid)); ra = std(cleaned(mid) - clean(mid));
fprintf('  50 Hz interference: sd %.3f before, %.4f after the notch\n', rb, ra);
check(ra < 0.05 * rb, 'the notch removes mains interference'); disp('  check passed: notch');
if make_plots
  figure; plot(t, noisy, t, cleaned, t, clean, '--'); xlim([-30 30]); xlabel('time (ms)'); legend('with 50 Hz', 'notched', 'clean');
end
disp('All checks passed.');
