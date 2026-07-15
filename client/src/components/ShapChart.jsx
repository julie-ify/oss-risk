import {
	BarChart,
	Bar,
	XAxis,
	YAxis,
	CartesianGrid,
	Tooltip,
	ReferenceLine,
	ResponsiveContainer,
	Cell,
} from 'recharts';

const formatFeatureName = (name) => {
	return name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
};

const CustomTooltip = ({ active, payload }) => {
	if (!active || !payload?.length) return null;
	const d = payload[0].payload;
	return (
		<div className="bg-white border border-gray-200 rounded-lg p-3 text-xs shadow-sm max-w-xs">
			<p className="font-medium text-gray-900 mb-1">
				{formatFeatureName(d.feature)}
			</p>
			<p className="text-gray-600">
				Actual value:{' '}
				<span className="font-mono font-medium">{d.feature_value}</span>
			</p>
			<p className={d.shap >= 0 ? 'text-red-600' : 'text-green-700'}>
				SHAP: {d.shap >= 0 ? '+' : ''}
				{d.shap.toFixed(3)}
				<span className="text-gray-400 ml-1">
					({d.shap >= 0 ? 'pushes toward abandoned' : 'pushes toward active'})
				</span>
			</p>
		</div>
	);
};

const ShapChart = ({ shapValues }) => {
	const data = [...shapValues]
		.sort((a, b) => Math.abs(b.shap) - Math.abs(a.shap))
		.slice(0, 10)
		.reverse();

	const maxAbs = Math.max(...data.map((d) => Math.abs(d.shap)), 0.01);
	const domain = [-maxAbs * 1.1, maxAbs * 1.1];

	return (
		<div>
			<p className="text-xs text-gray-500 mb-3">
				Red bars increase abandonment risk · green bars reduce it
			</p>
			<ResponsiveContainer width="100%" height={data.length * 38 + 20}>
				<BarChart
					data={data}
					layout="vertical"
					margin={{ top: 0, right: 16, left: 8, bottom: 0 }}
				>
					<CartesianGrid
						horizontal={false}
						strokeDasharray="3 3"
						stroke="#f0f0f0"
					/>
					<XAxis
						type="number"
						domain={domain}
						tickFormatter={(v) => v.toFixed(2)}
						tick={{ fontSize: 11, fill: '#9ca3af' }}
						axisLine={false}
						tickLine={false}
					/>
					<YAxis
						type="category"
						dataKey="feature"
						tickFormatter={formatFeatureName}
						width={180}
						tick={{
							fontSize: 11,
							fill: '#6b7280',
							fontFamily: 'JetBrains Mono, monospace',
						}}
						axisLine={false}
						tickLine={false}
					/>
					<Tooltip content={<CustomTooltip />} cursor={{ fill: '#f9fafb' }} />
					<ReferenceLine x={0} stroke="#d1d5db" strokeWidth={1} />
					<Bar dataKey="shap" radius={[0, 3, 3, 0]}>
						{data.map((entry, i) => (
							<Cell
								key={i}
								fill={entry.shap >= 0 ? '#cf222e' : '#1a7f37'}
								fillOpacity={0.85}
							/>
						))}
					</Bar>
				</BarChart>
			</ResponsiveContainer>
		</div>
	);
};

export default ShapChart;
