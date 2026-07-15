const ModelInfo = ({ threshold }) => {
	return (
		<div
			className="border-t border-gray-100 bg-gray-50 px-6 py-3
                    flex flex-col sm:flex-row justify-between gap-2 text-xs text-gray-400"
		>
			<span>
				Model: Random Forest · trained on 18,326 PyPI repos (created 2020) ·
				decision threshold {threshold}
			</span>
			<span className="sm:text-right max-w-sm">
				Predictions are probabilistic estimates based on early-lifecycle
				signals. Not a guarantee of future maintenance status.
			</span>
		</div>
	);
};

export default ModelInfo;
