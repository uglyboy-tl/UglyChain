import sys

from loguru import logger

from uglychain import Model, finish, run_function
from uglychain.llm import FunctionCall
from uglychain.woker.code_interpreter import CodeInterpreter, run_code

logger.remove()
logger.add(sink=sys.stdout, level="TRACE")

worker = CodeInterpreter(model=Model.GPT3_TURBO)
#input = "我买房贷款了187万，贷款的年利率是4.9%，贷款期限是30年，每月还款多少？"
input = """
我安装了这些软件包：
```
cpp-11 g++-11 gcc-11 gcc-11-base libaccinj64-11.8 libasan6 libcu++-dev libcub-dev libcublas11
libcublaslt11 libcuda1 libcudart11.0 libcufft10 libcufftw10 libcuinj64-11.8 libcupti-dev
libcupti11.8 libcurand10 libcusolver11 libcusolvermg11 libcusparse11 libgcc-11-dev libnppc11
libnppial11 libnppicc11 libnppidei11 libnppif11 libnppig11 libnppim11 libnppist11 libnppisu11
libnppitc11 libnpps11 libnvblas11 libnvidia-ml-dev libnvidia-ptxjitcompiler1 libnvjpeg11
libnvrtc-builtins11.8 libnvrtc11.2 libnvtoolsext1 libnvvm4 libstdc++-11-dev libthrust-dev libtsan0
nvidia-cuda-dev nvidia-opencl-dev nvidia-profiler ocl-icd-opencl-dev opencl-c-headers
opencl-clhpp-headers
```
随后又卸载了这些软件包：
```
g++-11* libaccinj64-11.8* libcu++-dev* libcub-dev* libcublas11* libcublaslt11* libcudart11.0*
libcufft10* libcufftw10* libcuinj64-11.8* libcupti-dev* libcupti11.8* libcurand10* libcusolver11*
libcusolvermg11* libcusparse11* libnppc11* libnppial11* libnppicc11* libnppidei11* libnppif11*
libnppig11* libnppim11* libnppist11* libnppisu11* libnppitc11* libnpps11* libnvblas11*
libnvidia-ml-dev* libnvjpeg11* libnvrtc-builtins11.8* libnvrtc11.2* libnvtoolsext1* libnvvm4*
libstdc++-11-dev* libthrust-dev* nvidia-cuda-dev* nvidia-cuda-toolkit* nvidia-opencl-dev*
nvidia-profiler* ocl-icd-opencl-dev* opencl-c-headers* opencl-clhpp-headers*
```

帮我看看我安装的这些软件包中还有哪些软件包没卸载？
"""
response = worker.run(input)
logger.info(worker.run(input))
assert isinstance(response, FunctionCall)
# assert isinstance(response.args["language"], Language)
logger.info(run_function([run_code, finish], response))
