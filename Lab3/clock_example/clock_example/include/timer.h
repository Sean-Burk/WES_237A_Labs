
#ifndef __TIMER_H__
#define __TIMER_H__

#include <time.h>


class LinuxTimer
{

public:
	LinuxTimer(){ clock_gettime( CLOCK_MONOTONIC, &start_); }

	void start(){ clock_gettime( CLOCK_MONOTONIC, &start_); }

	void stop(){ clock_gettime( CLOCK_MONOTONIC, &stop_); }

	size_t getElapsed()
	{
		size_t accum = ( stop_.tv_sec - start_.tv_sec ) * 1000000000L
			+ ( stop_.tv_nsec - start_.tv_nsec );

		return accum;
	}

private:
	struct timespec start_;
	struct timespec stop_;

};


#endif // __TIMER_H__

