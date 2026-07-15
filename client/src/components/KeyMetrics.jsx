const KeyMetrics = ({ metrics }) => {
	const items = [
		{ label: 'Commits (6 mo)', value: metrics.commits },
		{ label: 'Contributors', value: metrics.contributors },
		{ label: 'Active weeks', value: `${metrics.active_weeks} / 26` },
		{ label: 'Stars', value: metrics.stars },
		{ label: 'Forks', value: metrics.forks },
		{ label: 'Releases', value: metrics.releases },
		{ label: 'Issues opened', value: metrics.issues_opened },
		{ label: 'PRs opened', value: metrics.prs_opened },
	];

	return (
		<div className="grid grid-cols-4 gap-3">
			{items.map(({ label, value }) => (
				<div
					key={label}
					className="bg-gray-50 border border-gray-100 rounded-xl p-3"
				>
					<p className="text-xs text-gray-500 mb-1">{label}</p>
					<p className="text-lg font-semibold text-gray-900 font-mono">
						{value}
					</p>
				</div>
			))}
		</div>
	);
};

export default KeyMetrics;
