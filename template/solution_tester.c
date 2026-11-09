#include <omp.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>

#include "merge.h"
#include "exclusive_scan.h"

void fill_array(int *a, int n) {
  srand(0);
  for (int i = 0; i < n; i++) {
    a[i] = rand() & 31;
  }
}

void seq_merge(double a[], long n, double b[], long m, double c[]){
  long i, j, k;
  
  i = 0;
  j = 0;
  k = 0;

  while (i < n && j < m) {
    c[k++] = (a[i] <= b[j]) ? a[i++] : b[j++];
  }

  while (i < n) {
    c[k++] = a[i++];
  }

  while (j < m) {
    c[k++] = b[j++];
  }

}

static int cmpfunc(const void * a, const void * b) {
  return (*(double*) a - *(double*) b);
}

void test_merge(int n, int m) {
  double *a, *b, *c; 
  a = (double*)calloc(n, sizeof(double));
  b = (double*)calloc(m, sizeof(double));
  c = (double*)calloc(n+m, sizeof(double));

  int i;
  #pragma omp parallel for
  for(i=0; i<n; i++) {
    a[i] = 2*i+1;
  }

  #pragma omp parallel for
  for(i=0; i<m; i++) {
    b[i] = 2*i;
  }

  double *res = (double*)calloc(n+m, sizeof(double));

  memcpy(res, a, n*sizeof(double));
  
  memcpy(res+n, b, m*sizeof(double));

  qsort(res, n+m, sizeof(double), cmpfunc);
  
  double time = omp_get_wtime();
  merge(a, n, b, m, c);
  time = omp_get_wtime() - time;
  int ok = 1;
  for (i = 0; i < n+m; i++) {
  if (res[i] != c[i]) {
      
	    printf("Merge: Test error at element %ld: %g should be %g\n", i, res[i], c[i]);
  	  ok = 0;
	    break;
    }
  }
  
  if( ok ) {
    printf("PASSED\n");
  }
  free(a);
  free(b);
  free(c);
  free(res);
  printf("Execution time: %10.6f", time);
  
}

void scan(int A[], int n) {
  if (n == 1) return;
  
  int *B = malloc((n>>1) * sizeof(int));
  int i;
  
  for (i = 0; i < (n>>1); i++)
    B[i] = A[i<<1] + A[(i<<1) + 1];
  
  scan(B, n>>1);
  
  A[1] = B[0];
  for (i = 1; i < (n>>1); i++) { A[i<<1] += B[i-1];
    A[(i<<1) + 1] = B[i];
  }
  
  if (n & 1) A[n - 1] = B[(n>>1) - 1] + A[n - 1];
  
  free(B);
}

void test_exclusive_scan() {
  int n = 1000000;
  int* A = malloc(n * sizeof(int));
  fill_array(A, n);

  double time = omp_get_wtime();
  exclusive_scan(A, n);
  time = omp_get_wtime() - time;

  int *Q = malloc(n * sizeof(int));
  int i;
  fill_array(Q, n);
  scan(Q, n);
  for (i = n-1; i > 0; i--) {
     Q[i] = Q[i - 1];
  }
  Q[0] = 0;
    
  int ok = 1;
  for (i = 0; i < n; i++) {
  if (A[i] != Q[i]) {
	    printf("Scan: Test error at element %d: %d should be %d\n", i, A[i], Q[i]);
  	  ok = 0;
	    break;
    }
  }
  if( ok ) {
    printf("PASSED\n");
  }
  free(Q);  

  printf("Execution time: %10.6f", time);
}

int main(int argc, char* argv[]) {
  
  if(argc != 2) {
    printf("please specify what algorithm should be tested (merge or scan)");
    exit(0);
  }
  if(strcmp(argv[1],"merge") == 0) {
    test_merge(10000, 10000);
  }
  if(strcmp(argv[1],"scan") == 0) {
    test_exclusive_scan();
  }
  

}

