import os
import sys
# import argparse
from datetime import datetime 
import openai
from openai import OpenAI

import subprocess
import numpy as np


def pass_at_k(n, c, k): 
    #  total number of samples
    #  number of correct samples
    #  k in pass@$k$

    if n - c < k: return 1.0
    return 1.0 - np.prod(1.0 - k /
        np.arange(n - c + 1, n + 1))

def print_stats(pass_k, passed, model, algorithm, runs):
    with open("statistics", "w") as stats:
        stats.write("model: " + str(model) + "\n")
        stats.write("algorithm: " + str(algorithm) + "\n")
        stats.write("runs: " + str(runs))
        stats.write("passed: " + str(passed) + "\n")
        stats.write("pass@k: " + str(pass_k))

    print("passed: " + str(passed))
    print("pass@k: " + str(pass_k))


class ChatGPTHarness:
    client = None
    def __init__(self):    
        ChatGPTHarness.client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY")
        )


    def run_merge(self, model=None, runs=None, template_dir="./template"):
        if model is None:
            model = "gpt-4o"
        if runs is None:
            runs = 1
        current_time = datetime.now()
        passed = 0
        for i in range(runs):
            run = str(i+1)
            print("starting run " + run)
            dir_name = "merge-" + current_time.strftime('%d.%m.%Y.%h.%s') + "-run:"+run
            os.mkdir(dir_name)
            os.system("cp " + template_dir + "/* " + dir_name)
            os.chdir(dir_name)
            with open("merge_prompt", 'r') as prompt_file:
                prompt = prompt_file.read()
            try:
                merge_response = self.client.responses.create(
                    model=model,
                    instructions="You are given C code that you have to parallelize using OpenMP. Your response should consist only of your solution. The name and signature of the function must not change. You must include all the imports in the given code. Do not include any markdown symbols in your response.",
                    input=prompt
                )
            except openai.BadRequestError:
                print("run "+ run + " could not retrieve model answer (Bad Request)")
                os.chdir("..")
                continue
            except openai.AuthenticationError:
                print("run " + run + " could not retrieve model answer (Authentication failed)")
                os.chdir("..")
                continue
            with open("merge.c", 'w') as solution:
                solution.write(merge_response.output_text)

            print("compiling solution...")

            os.system("make")

            print("testing solution...")

            try:
                result = subprocess.run(["./solution_tester", "merge"], capture_output=True, timeout=30)

                if "PASSED" in result.stdout.decode('utf-8'):
                    passed = passed+1
                    print("PASSED")

                with open("result", 'w') as result_file:
                    result_file.write(result.stdout.decode('utf-8'))

                with open("errors", 'w') as error_file:
                    error_file.write(result.stderr.decode('utf-8'))

                print("run "+ run + " complete")

            except subprocess.TimeoutExpired:
                print("run " + run + " timed out while testing")
                with open("result", 'w') as result_file:
                    result_file.write("Timed out")

            except FileNotFoundError:
                print("compilation failed (no executable found)")
                with open("result", 'w') as result_file:
                    result_file.write("No executable found")

            finally:
                os.chdir("..")
        k = runs/2
        print_stats(pass_at_k(runs, passed, max(k, 1)), passed, model, "merge", runs)

    def run_scan(self, model=None, runs=None, template_dir="./template"):
        base_dir = os.getcwd()

        if model is None:
            model = "gpt-4o"
        if runs is None:
            runs = 1
        current_time = datetime.now()
        passed = 0
        for i in range(runs):
            run = str(i+1)
            print("starting run " + run)
            dir_name = "runs/" + model + "/scan-" + current_time.strftime('%d.%m.%Y.%h.%s') + "-run:" + run
            
            os.makedirs(dir_name)
            os.system("cp " + template_dir + "/* " + dir_name)
            os.chdir(dir_name)
            os.system("pwd")
            with open("scan_prompt", 'r') as prompt_file:
                prompt = prompt_file.read()
            print("prompting AI...")
            try:
                scan = self.client.responses.create(
                    model=model,
                    instructions="You are given C code that you have to parallelize using OpenMP. Your response should consist only of your solution. The name and signature of the function must not change. You must include all the imports in the given code. Do not include any markdown symbols in your response.",
                    input=prompt
                )
            except openai.BadRequestError:
                print("run "+ run + " could not retrieve model answer (Bad Request)")
                os.chdir(base_dir)
                continue
            except openai.AuthenticationError:
                print("run " + run + " could not retrieve model answer (Authentication failed)")
                os.chdir(base_dir)
                continue
            with open("exclusive_scan.c", 'w') as solution:
                solution.write(scan.output_text)

            print("compiling solution...")

            os.system("make")

            print("testing solution...")

            try:
                result = subprocess.run(["./solution_tester", "scan"], capture_output=True, timeout=30)

                if "PASSED" in result.stdout.decode('utf-8'):
                    passed = passed+1
                    print("PASSED")

                with open("result", 'w') as result_file:
                    result_file.write(result.stdout.decode('utf-8'))

                with open("errors", 'w') as error_file:
                    error_file.write(result.stderr.decode('utf-8'))

                print("run "+ run + " complete")

            except subprocess.TimeoutExpired:
                print("run " + run + " timed out while testing")
                with open("result", 'w') as result_file:
                    result_file.write("Timed out")

            except FileNotFoundError:
                print("compilation failed (no executable found)")
                with open("result", 'w') as result_file:
                    result_file.write("No executable found")

            finally:
                os.system("make remove-template")
                os.chdir(base_dir)
        k = runs/2
        print_stats(pass_at_k(runs, passed, max(k, 1)), passed, model, "scan", runs)

