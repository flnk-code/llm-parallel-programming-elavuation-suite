CC = gcc
OBJECTS = merge.o exclusive_scan.o solution_tester.o

solution_tester: $(OBJECTS)
	$(CC) $(OBJECTS) -o solution_tester -fopenmp 

%.o: %.c
	$(CC) -c $< -lpthread -fopenmp

remove-template:
	rm -f *.o *.h scan_prompt merge_prompt Makefile

clean:
	rm -f merge.o exclusive_scan.o solution_tester.o solution_tester
