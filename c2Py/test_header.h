// This is a test file for c2Py.py
// Author: Charles Machalow

#include <iostream>
#include <string>

typedef char CHAR;
typedef unsigned char BYTE;
#define MYTYPE int

int main()
{
	std::cout << "Hi" << std::endl;
	return 1;
}

struct a {
	CHAR c;
	BYTE d;
} ;

typedef struct s {
	byte a[3];
	unsigned int b : 4;
}_s, *Ps;

typedef union u {
	byte a[4];
	long b;
}u;


// TODO move this inside an existing struct to work on nesting
struct {
	byte e : 4;
	byte f : 4;
	MYTYPE g;
};