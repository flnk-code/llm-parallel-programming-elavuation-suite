from chat_gpt_harness import ChatGPTHarness


 
def generate_and_test():
    vendor = input("What LLM would you like to test? \n [c]hatgpt   [g]emini \n")
    model = input("Please specify what model you want to use (leave empty for default): \n")
    print(model)
    if(model == ''):
        model = None
    algorithm = input("What algorithm do you want to test? \n [s]can    [m]erge \n")
    runs_string = input("How many solutions should be queried from the LLM? \n")
        
    runs = int(runs_string)
    match vendor:
        case "c":
            harness = ChatGPTHarness()
        case "g":
            from gemini_harness import GeminiHarness
            harness = GeminiHarness()

    match algorithm:
        case "s":
            harness.run_scan(model=model, runs=runs)   
   


if __name__ == "__main__":
    generate_and_test()