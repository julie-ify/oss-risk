import RiskDial from './RiskDial.jsx';
import ShapChart from './ShapChart.jsx';
import StructuralFlags from './StructuralFlags.jsx';
import KeyMetrics from './KeyMetrics.jsx';
import ModelInfo from './ModelInfo.jsx';

const Card = ({ title, children }) => {
	return (
		<div className="bg-white border border-gray-100 rounded-2xl overflow-hidden">
			<div className="px-6 py-4 border-b border-gray-100">
				<h2 className="text-sm font-semibold text-gray-700">{title}</h2>
			</div>
			<div className="px-6 py-5">{children}</div>
		</div>
	);
};

const ResultCard = ({ data }) => {
	const { repo, repo_url, meta, prediction } = data;
	const { risk_score, verdict, threshold, shap_values } = prediction;

	const verdictBorder =
		{
			'Low risk': 'border-green-200 bg-green-50',
			'Medium risk': 'border-amber-200 bg-amber-50',
			'High risk': 'border-red-200 bg-red-50',
		}[verdict] ?? 'border-gray-200 bg-gray-50';

	const verdictText =
		{
			'Low risk': 'text-green-800',
			'Medium risk': 'text-amber-800',
			'High risk': 'text-red-800',
		}[verdict] ?? 'text-gray-800';

	return (
		<div className="flex flex-col gap-4">
			<div
				className={`rounded-2xl border p-5 flex flex-col sm:flex-row
                       items-start sm:items-center gap-5 ${verdictBorder}`}
			>
				<RiskDial score={risk_score} verdict={verdict} />

				<div className="flex-1 min-w-0">
					<a
						href={repo_url}
						target="_blank"
						rel="noopener noreferrer"
						className={`text-xl font-semibold font-mono hover:underline
                        truncate block ${verdictText}`}
					>
						{repo}
					</a>
					{meta.description && (
						<p className="text-sm text-gray-600 mt-1 line-clamp-2">
							{meta.description}
						</p>
					)}
					<div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-gray-500">
						<span>
							Created:{' '}
							{new Date(meta.created_at).toLocaleDateString('en-GB', {
								month: 'short',
								year: 'numeric',
							})}
						</span>
						<span>Language: {meta.language}</span>
						<span>Owner: {meta.owner_type}</span>
						<span>Observation window: {meta.observation_window}</span>
					</div>
				</div>
			</div>

			{/* ── Key metrics ── */}
			<Card title="Activity in the first 6 months">
				<KeyMetrics metrics={meta.key_metrics} />
			</Card>

			{/* ── SHAP chart ── */}
			<Card title="What drove this prediction (SHAP feature contributions)">
				<ShapChart shapValues={shap_values} />
			</Card>

			{/* ── Structural flags ── */}
			<Card title="Structural compliance at the 6-month mark">
				<StructuralFlags flags={meta.structural_flags} />
			</Card>

			{/* ── Model info bar ── */}
			<div className="bg-white border border-gray-100 rounded-2xl overflow-hidden">
				<ModelInfo threshold={threshold} />
			</div>
		</div>
	);
};

export default ResultCard;
