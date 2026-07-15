import { useState } from 'react';
import SearchBar from './components/SearchBar.jsx';
import ResultCard from './components/ResultCard.jsx';
import { fetchPrediction } from './api/api.js';
import ErrorBanner from './components/ErrorBanner.jsx';
import LoadingState from './components/LoadingState.jsx';
import Hero from './components/Hero.jsx';

const App = () => {
	const [loading, setLoading] = useState(false);
	const [result, setResult] = useState(null);
	const [error, setError] = useState(null);

	async function handleSearch(input) {
		setLoading(true);
		setError(null);
		setResult(null);

		try {
			const data = await fetchPrediction(input);
			setResult(data);
		} catch (err) {
			setError(err.message || 'Something went wrong. Please try again.');
		} finally {
			setLoading(false);
		}
	}

	function handleReset() {
		setResult(null);
		setError(null);
	}

	return (
		<div className="min-h-screen bg-gray-50">
			{/* ── Nav ── */}
			<nav className="bg-white border-b border-gray-100 sticky top-0 z-10">
				<div className="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
					<button
						onClick={handleReset}
						className="flex items-center gap-2 hover:opacity-75 transition"
						aria-label="Go to home"
					>
						<span
							className="w-6 h-6 bg-navy-900 rounded-md flex items-center
                             justify-center text-white text-xs font-bold"
						>
							R
						</span>
						<span className="text-sm font-semibold text-gray-900">
							OSS Risk
						</span>
					</button>
					<span className="text-xs text-gray-400">
						Masters research project
					</span>
				</div>
			</nav>

			{/* ── Main ── */}
			<main className="max-w-3xl mx-auto px-4 py-10">
				{!result && <Hero />}

				<div className={result ? 'mb-6' : 'mb-0'}>
					<SearchBar onSearch={handleSearch} loading={loading} />
				</div>

				{/* Error */}
				{error && (
					<ErrorBanner message={error} onDismiss={() => setError(null)} />
				)}

				{/* Loading */}
				{loading && <LoadingState />}

				{/* Result */}
				{!loading && result && (
					<div>
						<div className="flex items-center justify-between mb-4">
							<p className="text-sm text-gray-500">
								Results for{' '}
								<span className="font-mono font-medium text-gray-800">
									{result.repo}
								</span>
							</p>
							<button
								onClick={handleReset}
								className="text-xs text-gray-400 hover:text-gray-700
                           border border-gray-200 rounded-lg px-3 py-1.5 transition"
							>
								← New search
							</button>
						</div>
						<ResultCard data={result} />
					</div>
				)}
			</main>

			<footer className="text-center py-8 text-xs text-gray-300">
				Built as part of a masters dissertation · predictions are probabilistic
				estimates only
			</footer>
		</div>
	);
};

export default App;
