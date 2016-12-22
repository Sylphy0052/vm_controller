'''impl

add(ip)
info()
start(id)
clone(vmid, id)
migrate(vmid, id)
get_info()
get_vm_info()
get_vm_info_by_id(id)
get_cpu_larger_than_val(val)
get_mem_larger_than_val(val)
get_cpu_least()
get_mem_least()
'''

import vmcontroller as vm

if __name__ == '__main__':

	while True:

		for data in vm.get_cpu_larger_than_val(70):
			from_id = vm.get_vm_info_by_id(data.id)
			to_id = vm.get_cpu_least().id
			migrate(from_id, to_id)

