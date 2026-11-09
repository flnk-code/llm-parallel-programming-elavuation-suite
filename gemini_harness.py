import os
import sys
import argparse
from datetime import datetime 
from google import genai
from google.genai import types
from google.genai import errors
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
class GeminiHarness:
    client = None
    def __init__(self):
        self.client = genai.Client()

    def run_merge(self, model=None, runs=None, template_dir="./template"):
        base_dir = os.getcwd()
        if model is None:
            model = "gemini-3.8-flash"
        if runs is None:
            runs = 1
        current_time = datetime.now()
        passed = 0
        for i in range(runs):
            run = str(i+1)
            print("starting run " + run)
            dir_name = "runs/merge/" + model + "/merge-" + current_time.strftime('%d.%m.%Y.%h.%s') + "-run:" + run
            os.makedirs(dir_name)
            os.system("cp " + template_dir + "/* " + dir_name)
            os.chdir(dir_name)
            with open("merge_prompt", 'r') as prompt_file:
                prompt = prompt_file.read()
            print("prompting AI...")
            try:
                merge_response = self.client.models.generate_content(
                    model=model,
                    config=types.GenerateContentConfig(system_instruction="You are given C code that you have to parallelize using OpenMP. Your response should consist only of your solution. The name and signature of the function must not change. You must include all the imports in the given code. Do not include any markdown symbols in your response."),
                    contents=prompt
                )
            except errors.APIError as e:
                print(e.code) # 404
                print(e.message)
                os.chdir(base_dir)
                continue
            except Exception as e:
                print(e)
                os.chdir(base_dir)
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
                self.client.close()
                os.chdir(base_dir)
        k = runs/2
        print_stats(pass_at_k(runs, passed, max(k, 1)), passed, model, "merge", runs)

    def run_scan(self, model=None, runs=None, template_dir="./template"):
        base_dir = os.getcwd()
        if model is None:
            model = "gemini-3.8-flash"
        if runs is None:
            runs = 1
        current_time = datetime.now()
        passed = 0
        for i in range(runs):
            run = str(i+1)
            print("starting run " + run)
            dir_name = "runs/scan/"+model+"/scan-"+current_time.strftime('%d.%m.%Y.%h.%s') + "-run:"+run
            os.makedirs(dir_name)
            os.system("cp " + template_dir + "/* " + dir_name)
            os.chdir(dir_name)
            with open("scan_prompt", 'r') as prompt_file:
                prompt = prompt_file.read()
            print("prompting AI...")
            try:
                scan = self.client.models.generate_content(
                    model=model,
                    config=types.GenerateContentConfig(system_instruction="You are given C code that you have to parallelize using OpenMP. Your response should consist only of your solution. The name and signature of the function must not change. You must include all the imports in the given code. Do not include any markdown symbols in your response."),
                    contents=prompt
                )
            except errors.APIError as e:
                print(e.code) # 404
                print(e.message)
                os.chdir(base_dir)
                continue
            except Exception as e:
                print(e)
                os.chdir(base_dir)
                continue
            with open("exclusive_scan.c", 'w') as solution:
                solution.write(scan.text)

            # except openai.BadRequestError:
            #     print("run "+ run + " could not retrieve model answer (Bad Request)")
            #     os.chdir("..")
            #     continue
            # except openai.AuthenticationError:
            #     print("run " + run + " could not retrieve model answer (Authentication failed)")
            #     os.chdir("..")
            #     continue

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
    
        self.client.close()
        k = runs/2
        print_stats(pass_at_k(runs, passed, max(k, 1)), passed, model, "scan", runs)
