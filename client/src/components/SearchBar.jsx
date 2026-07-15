import { useState } from 'react';

const SearchBar = ({ onSearch, loading }) => {
	const [value, setValue] = useState('');

	function handleSubmit(e) {
		e.preventDefault();
		const trimmed = value.trim();
		if (trimmed) onSearch(trimmed);
	}

	return (
		<form onSubmit={handleSubmit} className="w-full">
			<div className="flex gap-3">
				<div className="relative flex-1">
					<svg
						className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4 pointer-events-none"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						strokeWidth={2}
					>
						<path
							strokeLinecap="round"
							strokeLinejoin="round"
							d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z"
						/>
					</svg>
					<input
						type="text"
						value={value}
						onChange={(e) => setValue(e.target.value)}
						placeholder="GitHub URL or PyPI package name — e.g. requests, https://github.com/owner/repo"
						className="w-full pl-10 pr-4 py-3 bg-white border border-gray-200
                       rounded-xl text-sm text-gray-900 placeholder-gray-400
                       focus:outline-none focus:ring-2 focus:ring-navy-800 focus:border-transparent
                       font-mono transition"
						disabled={loading}
						aria-label="Enter a GitHub repository URL or PyPI package name"
					/>
				</div>
				<button
					type="submit"
					disabled={loading || !value.trim()}
					className="px-6 py-3 bg-navy-900 text-white text-sm font-medium
                     rounded-xl hover:bg-navy-800 disabled:opacity-50
                     disabled:cursor-not-allowed transition whitespace-nowrap"
				>
					{loading ? (
						<span className="flex items-center gap-2">
							<svg
								className="animate-spin w-4 h-4"
								viewBox="0 0 24 24"
								fill="none"
							>
								<circle
									className="opacity-25"
									cx="12"
									cy="12"
									r="10"
									stroke="currentColor"
									strokeWidth="4"
								/>
								<path
									className="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8v8H4z"
								/>
							</svg>
							Analysing…
						</span>
					) : (
						'Analyse risk'
					)}
				</button>
			</div>
		</form>
	);
};

export default SearchBar;
