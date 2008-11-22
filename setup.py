"""Setup script for pympler.

To include the compiled html documentation right in the doc/, all html files from
`compiled_doc_dir` are moved directly into the `doc_dir`, the setup is executed, and
the files are removed afterwards.

"""
from distutils.core   import setup
from distutils.errors import DistutilsExecError
from distutils.spawn  import spawn  # raises DistutilsExecError

import pympler.metadata as metadata
import os, sys

def run_setup():
    setup(name=metadata.project_name,
          description=metadata.description,
          long_description = metadata.long_description,

          author=metadata.author,
          author_email=metadata.author_email,
          url=metadata.url,
          version=metadata.version,

          packages=['pympler',
                    'pympler.asizeof', 'pympler.heapmonitor',
                    'pympler.muppy', 'pympler.objects',
                    'test', 'test.asizeof', 'test.heapmonitor', 'test.muppy'],
          
          license=metadata.license,
          platforms = ['any'],
          classifiers=['Development Status :: 3 - Alpha',
                       'Environment :: Console',
                       'Intended Audience :: Developers',
                       'License :: OSI Approved :: Apache Software License',
                       'Operating System :: OS Independent',
                       'Programming Language :: Python',
                       'Topic :: Software Development :: Bug Tracking',
                       ],
          )

_test = {'try':  '-pre-install',
         'test': '-post-install'}

if len(sys.argv) > 1 and sys.argv[1] in _test:
     # invoke  ./test/runtest.py -[pre|post]-install ...
     # to run the unittests before or after installation
    args = [sys.executable,  # this Python binary
            os.path.join('test', 'runtest.py'),
           _test[sys.argv[1]]]
    args.extend(sys.argv[2:])
    try:
        sys.exit(spawn(args))
    except DistutilsExecError:
        print("\nError: test failed or did not run.  Try '... %s -verbose 3'" % ' '.join(sys.argv))
        sys.exit(1)
else:
    run_setup()
