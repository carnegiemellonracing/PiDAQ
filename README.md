# PiDAQ

**PiDAQ**: A Raspberry **Pi**-based **Data Acquisition** system for Carnegie Mellon Racing. Designed for 24e and 25e EV racecars.

## Design choices for cleanup code:

Copy pasted dependencies into own code (we want to do this so that A, there’s less useless clutter, and B, best practices to not have as much external dependencies, and C, we’re able to change the way they do things that we don’t like such as their sleep)

Took out useless stuff that doesn’t apply to us (such as other sensors under the same brand) and fixed up some of their logic that included sleeping bc that gates the rest of the thread

In each, wrote up a main file that describes how it’ll be used in the implementation

Wrote main file where used multiprocessing and Python threads to concurrently recieve multiple data and push to can 

Instead of making a can queue that stores info in a queue and then pushes to the can line, we just used a multiprocessing value because what if the can read is too slow and it backs up the queue and now you are reading values from way before. 

So now what we have is a shared value (variable) that is where the read value is held and the mcp reads that value. (it is indeed possible that the mcp reads at a frequency too fast so that the value is not updated with the real current value so can would read the same value twice but it’d be easier to work with than a backed up queue)

Modified CAN symbol file bc wanted to merge some msgs (each single message takes time → sending three 2 byte msgs is worse than one 6 byte msg bc each msgs also has header bytes (that contains info abt the msg) so it’s slower).

timeout is needed as it’s basically a limit to how long you want to keep trying until you just return None. That way, if it’s taking too long to grab the data, you can simply give up and return None so that it doesn’t gate others. It’s okay if you’re returning None a lot of the time cuz then you just don’t update the value.

Note that the i2c handle and spi handles are created outside of the class. This is future proofing so that they can still be used by other sensors in the future as if they are created in the class, no-one else can access them.