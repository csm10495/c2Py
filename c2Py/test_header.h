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

#if 1
	#ifndef THING_NOT_DEF
		struct a {
			CHAR c;
			BYTE d;
		} ;
	#endif

	typedef struct s {
		//Comment to remove.
		byte a[3]; // Comment to keep
		unsigned int b : 4;
	}_s, *Ps;

	typedef union u {
		byte a[4];
		long b;
	}u;

	// Test _volatile
	typedef volatile struct volatileStruct {
		#if 0
			volatile int volatileIntFromIf;
		#else
			volatile int volatileIntFromElse;
		#endif
	};

	#ifndef MYTYPE
		// TODO move this inside an existing struct to work on nesting
		struct {
			byte e : BITS_FOR_E;
			byte f : 8 - BITS_FOR_E;
			MYTYPE g;
		};
	#endif

#else
	typedef struct inElse {
		int a;
	};
#endif

