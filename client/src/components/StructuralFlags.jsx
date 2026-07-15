const FLAG_LABELS = {
	has_readme: 'README',
	has_license: 'Licence file',
	has_contributing: 'CONTRIBUTING guide',
	has_ci_cd: 'CI/CD config',
	has_setup_cfg_or_pyproject: 'Packaging file (setup / pyproject)',
	has_changelog: 'Changelog',
	has_dockerfile: 'Dockerfile',
	has_tests_dir: 'Tests directory',
	has_docs_dir: 'Docs directory',
	has_docs_config: 'Docs config (MkDocs / Sphinx)',
};

const Flag = ({ label, present }) => {
	return (
		<div className="flex items-center gap-2.5">
			<span
				className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 text-xs
          ${
						present ? 'bg-green-100 text-green-700' : 'bg-red-50 text-red-500'
					}`}
				aria-label={present ? 'Present' : 'Missing'}
			>
				{present ? '✓' : '✕'}
			</span>
			<span
				className={`text-sm ${present ? 'text-gray-700' : 'text-gray-400'}`}
			>
				{label}
			</span>
		</div>
	);
};

const StructuralFlags = ({ flags }) => {
	const entries = Object.entries(FLAG_LABELS);
	const presentCount = entries.filter(([key]) => flags[key]).length;

	return (
		<div>
			<p className="text-xs text-gray-500 mb-3">
				{presentCount} / {entries.length} compliance signals present at the
				6-month mark
			</p>
			<div className="grid grid-cols-2 gap-2">
				{entries.map(([key, label]) => (
					<Flag key={key} label={label} present={!!flags[key]} />
				))}
			</div>
		</div>
	);
};

export default StructuralFlags;
