"""Setup script for pympler.

To include the compiled html documentation right in the doc/, all html files from
`compiled_doc_dir` are moved directly into the `doc_dir`, the setup is executed, and
the files are removed afterwards.

"""
from distutils.core import setup
import os
import shutil

from pympler import metadata

doc_dir = 'doc'
compiled_doc_dir = os.path.join(doc_dir, 'build', 'html')

def copy_doc():
    """Copy all docs to root doc-directory.

    Returns a list of all copied files and directories.
    """
    res = []
    
    files = os.listdir(compiled_doc_dir)
    for entry in files:
        src = os.path.join(compiled_doc_dir, entry)
        dst = os.path.join(doc_dir, entry)
        if os.path.exists(dst):
            if os.path.isfile(dst):
                os.remove(dst)
            elif os.path.isdir(dst):
                shutil.rmtree(dst)
        if os.path.isfile(src):
            shutil.copy2(src, doc_dir)
        elif os.path.isdir(src):
            shutil.copytree(src, os.path.join(doc_dir, entry))
        else:
            raise ValueError, src + " is neither file nor directory"
        res.append(dst)
    return res

def del_copied_docs(files):
    """Delete all files."""
    for file in files:
        if os.path.isfile(file):
            os.remove(file)
        elif os.path.isdir(file):
            shutil.rmtree(file)
        else:
            raise ValueError, file + " is neither file nor directory"

def run_setup():
    setup(name=metadata.project_name,
          description=metadata.description,
          long_description = metadata.long_description,

          author=metadata.author,
          author_email=metadata.author_email,
          url=metadata.url,
          version=metadata.version,

          packages=['pympler',
                    'pympler.asizeof', 'pympler.heapmonitor', 'pympler.muppy',
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

if os.path.isdir(compiled_doc_dir):
    files = copy_doc()
    run_setup()
    del_copied_docs(files)
else:
    run_setup()
