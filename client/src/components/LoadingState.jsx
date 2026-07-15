import { useState } from 'react';

const LoadingState = () => {
	const steps = [
		'Resolving repository…',
		'Fetching commit history…',
		'Extracting issue and PR activity…',
		'Checking structural signals…',
		'Running model prediction…',
		'Computing SHAP explanations…',
	];
	const [step] = useState(() => {
		// rotate through steps every 3s — just show them all in a pulsing list
		return steps;
	});

	return (
		<div className="w-full max-w-3xl mx-auto mt-10 flex flex-col items-center gap-6">
			<div
				className="w-10 h-10 rounded-full border-4 border-navy-900 border-t-transparent
											animate-spin"
				aria-label="Loading"
			/>
			<div className="space-y-2 text-center">
				{steps.map((s, i) => (
					<p
						key={s}
						className="text-sm text-gray-400 animate-pulse"
						style={{ animationDelay: `${i * 0.15}s` }}
					>
						{s}
					</p>
				))}
			</div>
			<p className="text-xs text-gray-300 mt-2">
				This can take 30–90 seconds — the GitHub API is being queried in real
				time.
			</p>
		</div>
	);
};

export default LoadingState;
