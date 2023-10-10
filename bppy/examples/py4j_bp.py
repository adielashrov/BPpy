from py4j.java_gateway import JavaGateway
import sys
import os

dir_path = os.path.dirname(os.path.realpath(__file__))

gateway = JavaGateway.launch_gateway(classpath=os.path.join(dir_path, "BPjs-0.12.3.uber.jar"),
                                     die_on_exit=True,
                                     redirect_stdout=sys.stdout)

with open("HelloBPjsWorld.js", "r") as f:
    bprog = gateway.jvm.il.ac.bgu.cs.bp.bpjs.model.StringBProgram("my_bprogram", f.read())

runner = gateway.jvm.il.ac.bgu.cs.bp.bpjs.execution.BProgramRunner(bprog)
runner.addListener(gateway.jvm.il.ac.bgu.cs.bp.bpjs.execution.listeners.PrintBProgramRunnerListener())
runner.run()
