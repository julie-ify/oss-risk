const ErrorBanner = ({ message, onDismiss }) => {
	return (
		<div className="w-full max-w-3xl mx-auto mt-4">
			<div
				className="bg-red-50 border border-red-200 rounded-2xl px-5 py-4
											flex items-start justify-between gap-4"
			>
				<div className="flex gap-3 items-start">
					<span className="text-red-500 text-lg mt-0.5" aria-hidden="true">
						⚠
					</span>
					<p className="text-sm text-red-700">{message}</p>
				</div>
				<button
					onClick={onDismiss}
					className="text-red-400 hover:text-red-600 text-lg leading-none shrink-0"
					aria-label="Dismiss error"
				>
					×
				</button>
			</div>
		</div>
	);
};

export default ErrorBanner;
