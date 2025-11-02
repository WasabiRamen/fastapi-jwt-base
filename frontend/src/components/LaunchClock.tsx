import React, { useEffect, useRef, useState } from 'react';
import '../pages/Main.css';

const ENLIST_DATE = new Date('2024-12-30T00:00:00');
const DISCHARGE_DATE = new Date('2026-06-29T00:00:00');

export default function LaunchClock() {
  const [percent, setPercent] = useState<string>('0.00000000');
  const [fraction, setFraction] = useState<number>(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const start = ENLIST_DATE.getTime();
    const end = DISCHARGE_DATE.getTime();
    const total = Math.max(1, end - start);

    const update = () => {
      const now = Date.now();
      let f = (now - start) / total;
      if (f < 0) f = 0;
      if (f > 1) f = 1;
      setFraction(f);
      const pct = (f * 100).toFixed(8);
      setPercent(pct);
      rafRef.current = requestAnimationFrame(update);
    };

    rafRef.current = requestAnimationFrame(update);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  const mapToDay = (f: number) => {
    const dayMs = 24 * 60 * 60 * 1000;
    const t = f * dayMs;
    const hours = Math.floor(t / (60 * 60 * 1000)) % 24;
    const minutes = Math.floor(t / (60 * 1000)) % 60;
    const seconds = Math.floor(t / 1000) % 60;
    const ms = Math.floor(t % 1000);
    return { hours, minutes, seconds, ms };
  };

  const timeParts = mapToDay(fraction);

  const hourAngle = (fraction * 360) % 360;
  const minuteFraction = (fraction * 24) % 1 * 60;
  const minuteAngle = (minuteFraction / 60) * 360;
  const secondFraction = (minuteFraction % 1) * 60;
  const secondAngle = (secondFraction / 60) * 360;

  const pad = (n: number, d = 2) => n.toString().padStart(d, '0');

  return (
    <div className="launch-wrap">
      <div className="launch-inner">
        <section className="launch-progress">
          <h2 className="launch-title">서비스가 런칭 될 예정입니다</h2>
          <div className="progress-bar" aria-hidden>
            <div className="progress-fill" style={{ width: `${Math.min(100, Math.max(0, Number(percent)))}%` }} />
          </div>
          <div className="progress-info">
            <span className="percent">{percent}%</span>
            <span className="dates">{ENLIST_DATE.toLocaleDateString()} ▶ {DISCHARGE_DATE.toLocaleDateString()}</span>
          </div>
        </section>

        <section className="mil-clock">
          <h2 className="clock-title">HiLi의 국방부시계</h2>
          <div className="clock-and-readout">
            <div className="clock" role="img" aria-label="국방부시계">
              <div className="clock-face">
                <div className="hand hour" style={{ transform: `rotate(${hourAngle}deg)` }} />
                <div className="hand minute" style={{ transform: `rotate(${minuteAngle}deg)` }} />
                <div className="hand second" style={{ transform: `rotate(${secondAngle}deg)` }} />
                {Array.from({ length: 24 }).map((_, i) => {
                  const angle = (i / 24) * 360;
                  return (
                    <div key={i} className="tick" style={{ transform: `rotate(${angle}deg)` }}>
                      <div className="tick-line" />
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="clock-readout">
              <div className="digital">{pad(timeParts.hours)}:{pad(timeParts.minutes)}:{pad(timeParts.seconds)}.{timeParts.ms.toString().padStart(3,'0')}</div>
              <div className="fraction">진행률: {(fraction * 100).toFixed(8)}%</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
