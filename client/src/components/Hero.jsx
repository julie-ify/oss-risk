const Hero = () => {
	return (
		<div className="text-center mb-8">
			<div
				className="inline-flex items-center gap-2 bg-navy-900 text-white
											text-xs font-medium px-3 py-1.5 rounded-full mb-4"
			>
				<span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
				PyPI dependency health
			</div>
			<h1 className="text-3xl font-semibold text-gray-900 mb-2">
				OSS Abandonment Risk
			</h1>
			<p className="text-gray-500 text-base max-w-xl mx-auto">
				Predict whether a PyPI repository will be abandoned, using
				socio-technical signals from its first six months of development.
			</p>
		</div>
	);
};

export default Hero;
