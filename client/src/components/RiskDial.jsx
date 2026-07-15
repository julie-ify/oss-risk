import { useEffect, useRef } from 'react';

const RADIUS = 45;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

const verdictColors = (verdict) => {
	if (verdict === 'Low risk')
		return {
			stroke: '#1a7f37',
			text: 'text-green-700',
			bg: 'bg-green-50',
			border: 'border-green-200',
		};
	if (verdict === 'Medium risk')
		return {
			stroke: '#d97706',
			text: 'text-amber-700',
			bg: 'bg-amber-50',
			border: 'border-amber-200',
		};
	return {
		stroke: '#cf222e',
		text: 'text-red-700',
		bg: 'bg-red-50',
		border: 'border-red-200',
	};
};

const RiskDial = ({ score, verdict }) => {
	const arcRef = useRef(null);
	const colors = verdictColors(verdict);
	const targetOffset = CIRCUMFERENCE * (1 - score);

	useEffect(() => {
		if (!arcRef.current) return;
		arcRef.current.style.setProperty('--target-offset', targetOffset);
		arcRef.current.style.strokeDashoffset = CIRCUMFERENCE;
		void arcRef.current.getBoundingClientRect();
		arcRef.current.classList.add('score-arc');
	}, [score]);

	return (
		<div className="flex flex-col items-center gap-3">
			<div className="relative w-32 h-32">
				<svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
					<circle
						cx="50"
						cy="50"
						r={RADIUS}
						fill="none"
						stroke="#e5e7eb"
						strokeWidth="8"
					/>
					<circle
						ref={arcRef}
						cx="50"
						cy="50"
						r={RADIUS}
						fill="none"
						stroke={colors.stroke}
						strokeWidth="8"
						strokeLinecap="round"
						strokeDasharray={CIRCUMFERENCE}
						strokeDashoffset={CIRCUMFERENCE}
						style={{ '--target-offset': targetOffset }}
					/>
				</svg>
				<div className="absolute inset-0 flex flex-col items-center justify-center">
					<span className={`text-2xl font-semibold ${colors.text}`}>
						{Math.round(score * 100)}%
					</span>
					<span className="text-xs text-gray-400 mt-0.5">risk</span>
				</div>
			</div>

			<span
				className={`px-3 py-1 rounded-full text-sm font-medium border
                        ${colors.bg} ${colors.text} ${colors.border}`}
			>
				{verdict}
			</span>
		</div>
	);
};

export default RiskDial;
