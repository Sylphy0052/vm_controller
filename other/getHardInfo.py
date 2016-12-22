import psutil

for x in range(3):

	cpu = psutil.cpu_percent(interval=1)
	mem = psutil.virtual_memory().percent
	print("CPU: {0:.1f} MEM: {1:.1f}".format(cpu, mem))

