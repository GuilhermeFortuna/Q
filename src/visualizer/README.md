The project involves developing a desktop-based graphical user interface (GUI) application using Python, intended primarily for visualizing financial market data through candlestick charts. Its core functionality includes simulating and inspecting live market behavior, useful for both historical data analysis and real-time monitoring.

Key Objectives:

* **Desktop Application**: Pure Python implementation without browser dependencies, ensuring high performance, responsiveness.
* **GPU Acceleration**: Leverage an NVIDIA RTX 2060 GPU for rendering and computation to achieve high performance, smooth visuals, and minimal latency.
* **Candlestick Visualization**: High-quality, GPU-rendered candlestick charts with fluid, interactive capabilities, such as pan, zoom, real-time updates, and technical indicator overlays.
* **Live Market Simulation**: Capability to simulate live market data streams for testing strategies and inspecting market behavior in real-time conditions.
* **Data Integration**: Data to be plotted is originally in Pandas DataFrame format
* **Performance & Quality Priority**: Emphasis on delivering a visually appealing, polished user interface, coupled with robust performance metrics suitable for intensive, real-time market analysis scenarios.

Technical Considerations:

* **Recommended GUI Frameworks**: PySide6 with PyQtGraph for more native UI experience.
* **Concurrency Management**: Use Python's asyncio or multithreading to ensure smooth, non-blocking real-time data handling and GUI responsiveness.
* **GPU-Accelerated Computing**: Optionally incorporate CUDA-based libraries like CuPy for heavy numerical computations, further enhancing performance on supported hardware.

This application will serve as a tool that will be integrated with other projects I am developing, providing an efficient and visually appealing interface suitable for comprehensive market analysis and strategic decision-making. As well as market replay feature for testing strategies and inspecting market behavior in real-time conditions.
