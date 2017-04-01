// This is a test file for c2Py.py
// Author: Charles Machalow

#include <iostream>
#include <string>

typedef char CHAR
typedef unsigned char BYTE

int main()
{
	std::cout << "Hi" << std::endl;
	return 1;
}

typedef struct s {
	byte a[3];
	unsigned int b : 4;
	struct {
		byte c;
		byte d;
	};
}s;

struct a{
	byte c;
	byte d;
};