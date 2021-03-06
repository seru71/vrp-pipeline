#!/usr/bin/env python
"""

    vrp_pipeline.py
                        --run_folder PATH
                        [--settings PATH] 
                        [--log_file PATH]
                        [--verbose]
                        [--target_tasks]  (by default the last task in the pipeline)
                        [--jobs N]        (by default 1)
                        [--just_print]
                        [--flowchart]
                        [--key_legend_in_graph]
                        [--forced_tasks]
                        [--run_on_bcl_tile TILE_REGEX]

"""
import sys
import os
import glob


#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888

#   options


#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888


if __name__ == '__main__':
    from optparse import OptionParser
    import StringIO

    parser = OptionParser(version="%prog 1.0", usage = "\n\n    %prog --settings vrp_pipeline.config [--target_task TASK] [more_options]")
    
                                
    #
    #   general options: verbosity / logging
    #
    parser.add_option("-v", "--verbose", dest = "verbose",
                      action="count", 
                      help="Print more verbose messages for each additional verbose level.")
    parser.add_option("-L", "--log_file", dest="log_file",
                      metavar="FILE",
                      type="string",
                      help="Name and path of log file")


    #
    #   pipeline
    #
    parser.add_option("-s", "--settings", dest="pipeline_settings",
                        metavar="FILE",
                        type="string",
                        help="File containing all the settings for the analysis.")                  
    parser.add_option("-t", "--target_tasks", dest="target_tasks",
                        action="append",
                        metavar="JOBNAME",
                        type="string",
                        help="Target task(s) of pipeline.")
    parser.add_option("-j", "--jobs", dest="jobs",
                        metavar="N",
                        type="int",
                        help="Allow N jobs (commands) to run simultaneously.")
    parser.add_option("-n", "--just_print", dest="just_print",
                        action="store_true", 
                        help="Don't actually run any commands; just print the pipeline.")
    parser.add_option("--flowchart", dest="flowchart",
                        metavar="FILE",
                        type="string",
                        help="Don't actually run any commands; just print the pipeline "
                             "as a flowchart.")

    #
    #   Less common pipeline options
    #
    parser.add_option("--key_legend_in_graph", dest="key_legend_in_graph",
                        action="store_true",
                        help="Print out legend and key for dependency graph.")
    parser.add_option("--forced_tasks", dest="forced_tasks",
                        action="append",
                        metavar="JOBNAME",
                        type="string",
                        help="Pipeline task(s) which will be included even if they are up to date.")
    parser.add_option("--rebuild_mode", dest="rebuild_mode",
                        action="store_false", 
                        help="gnu_make_maximal_rebuild_mode")
    parser.add_option("--run_on_bcl_tile", dest="run_on_bcl_tile",
                        type="string",                        
                        help="Use only this tile when doing bcl2fastq conversion. For testing purposes.")
    
    parser.set_defaults(pipeline_settings=None, 
                        jobs=1, verbose=0, 
                        target_tasks=list(), forced_tasks=list(), 
                        just_print=False, key_legend_in_graph=False,
                        rebuild_mode=True, run_on_bcl_tile=None)
    

    # get help string
    f =StringIO.StringIO()
    parser.print_help(f)
    helpstr = f.getvalue()
    (options, remaining_args) = parser.parse_args()


    #vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    #                                             #
    #   Change this if necessary                  #
    #                                             #
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    #
    #   Add names of mandatory options,
    #       strings corresponding to the "dest" parameter
    #       in the options defined above
    #
    mandatory_options = ['pipeline_settings']

    #vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    #                                             #
    #   Change this if necessary                  #
    #                                             #
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


    def check_mandatory_options (options, mandatory_options, helpstr):
        """
        Check if specified mandatory options have been defined
        """
        missing_options = []
        for o in mandatory_options:
            if not getattr(options, o):
                missing_options.append("--" + o)
    
        if not len(missing_options):
            return
    
        raise Exception("Missing mandatory parameter%s: %s.\n\n%s\n\n" %
                        ("s" if len(missing_options) > 1 else "",
                         ", ".join(missing_options),
                         helpstr))
        
    check_mandatory_options(options, mandatory_options, helpstr)
            
    



#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888

#   Logger


#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888



if __name__ == '__main__':
    import logging
    import logging.handlers

    MESSAGE = 15
    logging.addLevelName(MESSAGE, "MESSAGE")

    def setup_std_logging (logger, log_file, verbose):
        """
        set up logging using programme options
        """
        class debug_filter(logging.Filter):
            """
            Ignore INFO messages
            """
            def filter(self, record):
                return logging.INFO != record.levelno

        class NullHandler(logging.Handler):
            """
            for when there is no logging
            """
            def emit(self, record):
                pass

        # We are interesting in all messages
        logger.setLevel(logging.DEBUG)
        has_handler = False

        # log to file if that is specified
        if log_file:
            handler = logging.FileHandler(log_file, delay=False)
            handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)6s - %(message)s"))
            handler.setLevel(MESSAGE)
            logger.addHandler(handler)
            has_handler = True

        # log to stderr if verbose
        if verbose:
            stderrhandler = logging.StreamHandler(sys.stderr)
            stderrhandler.setFormatter(logging.Formatter("    %(message)s"))
            stderrhandler.setLevel(logging.DEBUG)
            if log_file:
                stderrhandler.addFilter(debug_filter())
            logger.addHandler(stderrhandler)
            has_handler = True

        # no logging
        if not has_handler:
            logger.addHandler(NullHandler())


    #
    #   set up log
    #
    module_name = "vrp_pipeline"
    logger = logging.getLogger(module_name)
    setup_std_logging(logger, options.log_file, options.verbose)

    #
    #   Allow logging across Ruffus pipeline
    #
    def get_logger (logger_name, args):
        return logger

    from ruffus.proxy_logger import *
    (logger_proxy,
     logging_mutex) = make_shared_logger_and_proxy (get_logger,
                                                    module_name,
                                                    {})
    
    
    #vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv
    #                                             #
    #   Get pipeline settings from a config file  #
    #                                             #
    #^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    
    if not os.path.exists(options.pipeline_settings): 
        raise Exception('Provided settings file [%s] does not exist or cannot be read.' % options.pipeline_settings)

    import ConfigParser
    config = ConfigParser.ConfigParser()
    config.read(options.pipeline_settings)



    # Should dockerized execution be used?
    dockerize = True
    try:
        docker_bin = config.get('Docker','docker-binary')
        logger.info('Found docker-binary setting. Using dockerized execution mode.')
    except ConfigParser.NoOptionError:
        logger.info('Docker-binary setting is missing. Using regular execution mode.')
        dockerize = False
 

    # Get the pipeline input
    run_folder = None
    input_fastqs = None
    input_bams = None
    try:
	run_folder = config.get('Inputs','run-directory') 
	logger.info('Found run-directory setting. Starting from bcl2fastq conversion.')
        # check presence of the run folder, and sample sheet file
        if not os.path.exists(run_folder) or not os.path.exists(os.path.join(run_folder,'SampleSheet.csv')):
            raise Exception("Missing sample sheet file: %s.\n" % os.path.join(run_folder,'SampleSheet.csv'))
    except ConfigParser.NoOptionError:
        try:
            input_fastqs = os.path.join(runs_scratch_dir if dockerize else '', config.get('Inputs','input-fastqs'))
            input_fastqs_resolved = glob.glob(input_fastqs)
            if len(input_fastqs_resolved) < 2:
                raise Exception("Missing input FASTQs. Found %s FASTQ files in [%s].\n" % (len(input_fastqs_resolved), config.get('Inputs','input-fastqs')))
            logger.info('Found %s input FASTQs. Starting from read trimming.' % len(input_fastqs_resolved))
        except ConfigParser.NoOptionError:
            try:
                input_bams = os.path.join(runs_scratch_dir if dockerize else '', config.get('Inputs','input-bams'))
                input_bams_resolved = glob.glob(input_bams)
                if len(input_bams_resolved) < 1:
                    raise Exception("Missing input BAMs. Found %s BAM files in [%s].\n" % (len(input_bams_resolved), config.get('Inputs','input-bams')))
                logger.info('Found %s input BAMs. Starting from indexing BAMs.' % len(input_bams_resolved))
            except ConfigParser.NoOptionError:
	        raise Exception('Found no valid input setting in [%s]. Please provide one of [run_directory|input-fastqs|input-bams] in the pipeline settings file.' % options.pipeline_settings)


 


    # Root paths
    
    reference_root = config.get('Paths','reference-root')
    scratch_root = os.getcwd()
    try:
        scratch_root   = config.get('Paths','scratch-root')
    except ConfigParser.NoOptionError:
        logger.info('Scratch-root setting is missing. Using current directory: %s' % scratch_root)
    
    run_id = os.path.basename(run_folder) if run_folder != None else os.path.basename(scratch_root)
    runs_scratch_dir = os.path.join(scratch-root, run_id) if run_folder != None else scratch_root
    logger.info('Run\'s scratch directory: %s' % runs_scratch_dir)
      
    # optional results and fastq archive dirs  
    results_archive = None
    try:
        results_archive = config.get('Paths','results-archive')
    except ConfigParser.NoOptionError:
        logger.info('No results-archive provided. Results will not be archived outside of the run\'s scratch directory.')
    
    fastq_archive = None
    try:
        fastq_archive = config.get('Paths','fastq-archive')
    except ConfigParser.NoOptionError:
        logger.info('No fastq-archive provided. Fastq files will not be archived outside of the run\'s scratch directory.')

    
    # optional /tmp dir
    tmp_dir = None
    try:
        tmp_dir = config.get('Paths','tmp-dir')
    except ConfigParser.NoOptionError:
        logger.info('No tmp-dir provided. %s\'s /tmp will be used.' % ('Container' if dockerize else 'Execution host'))
    

    if dockerize:
        # Docker args
        docker_args = config.get('Docker', 'docker-args')
        docker_args += " -v " + ":".join([run_folder, run_folder,"ro"])
        docker_args += " -v " + ":".join([reference_root,reference_root,"ro"])
    
        # Mount archive dirs as files from them are read (linked fastqs, gvcfs). 
        # Archiving is not performed by docker, so no write access should be needed.
        if fastq_archive != None:
            docker_args += " -v " + ":".join([fastq_archive,fastq_archive,"ro"])
        if results_archive != None:
            docker_args += " -v " + ":".join([results_archive,results_archive,"ro"])
    
        # Tmp, if should be different than the default  
        if tmp_dir != None: 
            docker_args += " -v " + ":".join([tmp_dir,tmp_dir,"rw"])
            
        docker_args += " -v " + ":".join([runs_scratch_dir,runs_scratch_dir,"rw"])
        docker_args += " -w " + runs_scratch_dir
        docker = " ".join([docker_bin, docker_args]) 
    
    # set the default value if the tmp-dir was unset
    tmp_dir = "/tmp" if tmp_dir==None else tmp_dir
     
    
    # reference files
    reference = os.path.join(reference_root, config.get('Resources','reference-genome'))    
    host_genome = os.path.join(reference_root, config.get('Resources','host-genome'))     
    #filter_databases = [os.path.join(reference_root, db.strip()) for db in config.get('Resources','filter-databases').split(';'))]    
    silva_database = os.path.join(reference_root, config.get('Resources','silva-database'))     
    adapters = config.get('Resources', 'adapters-fasta')
    
    # tools
    bcl2fastq = config.get('Tools','bcl2fastq')
    bbmerge = config.get('Tools', 'bbmerge') 
    bbduk = config.get('Tools', 'bbduk')
    bwa = config.get('Tools', 'bwa')
    bedtools = config.get('Tools', 'bedtools')
    samtools = config.get('Tools', 'samtools')
    lofreq = config.get('Tools', 'lofreq')
    trimmomatic = config.get('Tools', 'trimmomatic') 
    fastqc = config.get('Tools', 'fastqc')
    spades = config.get('Tools', 'spades') 
    quast = config.get('Tools', 'quast')

#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888

#   Logger


#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888



if __name__ == '__main__':
    import logging
    import logging.handlers

    MESSAGE = 15
    logging.addLevelName(MESSAGE, "MESSAGE")

    def setup_std_logging (logger, log_file, verbose):
        """
        set up logging using programme options
        """
        class debug_filter(logging.Filter):
            """
            Ignore INFO messages
            """
            def filter(self, record):
                return logging.INFO != record.levelno

        class NullHandler(logging.Handler):
            """
            for when there is no logging
            """
            def emit(self, record):
                pass

        # We are interesting in all messages
        logger.setLevel(logging.DEBUG)
        has_handler = False

        # log to file if that is specified
        if log_file:
            handler = logging.FileHandler(log_file, delay=False)
            handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)6s - %(message)s"))
            handler.setLevel(MESSAGE)
            logger.addHandler(handler)
            has_handler = True

        # log to stderr if verbose
        if verbose:
            stderrhandler = logging.StreamHandler(sys.stderr)
            stderrhandler.setFormatter(logging.Formatter("    %(message)s"))
            stderrhandler.setLevel(logging.DEBUG)
            if log_file:
                stderrhandler.addFilter(debug_filter())
            logger.addHandler(stderrhandler)
            has_handler = True

        # no logging
        if not has_handler:
            logger.addHandler(NullHandler())


    #
    #   set up log
    #
    module_name = "exome"
    logger = logging.getLogger(module_name)
    setup_std_logging(logger, options.log_file, options.verbose)

    #
    #   Allow logging across Ruffus pipeline
    #
    def get_logger (logger_name, args):
        return logger

    from ruffus.proxy_logger import *
    (logger_proxy,
     logging_mutex) = make_shared_logger_and_proxy (get_logger,
                                                    module_name,
                                                    {})






#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888

#  Common functions 


#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888

import drmaa
drmaa_session = drmaa.Session()
drmaa_session.initialize()

from ruffus.drmaa_wrapper import run_job, error_drmaa_job

   
"""
cmd is given in a form:
    
    command {args}
    interpreter {interpreter_args} command {atgs}

The strings {args} and {interpreter_args} are replaced with args and interpreter_args values.
Examples of correct commands:
    cmd = "bcl2fastq {args}"
    cmd = "bcl2fastq -p param {args}"
    cmd = "bcl2fastq -p2 param {args} -p2 param2"
    cmd = "java {interpreter_args} -jar myjarfile.jar {args} -extras extra_arg
    cmd = "java -XmX4G {interpreter_args} -jar myjarfile.jar {args} -extras extra_arg
"""
def run_cmd(cmd, args, dockerize, interpreter_args=None, run_locally=True,
            cpus=1, mem_per_cpu=1024, walltime='24:00:00', 
            retain_job_scripts = True, job_script_dir = os.path.join(runs_scratch_dir, "drmaa")):
    
    full_cmd = ("{docker} "+cmd).format(docker = docker if dockerize else "",
                                        args=args, 
                                        interpreter_args = interpreter_args if interpreter_args!=None else "")

    stdout, stderr = "", ""
    job_options = "--ntasks=1 \
                   --cpus-per-task={cpus} \
                   --mem-per-cpu={mem} \
                   --time={time} \
                  ".format(cpus=cpus, mem=int(1.2*mem_per_cpu), time=walltime)
    #print full_cmd                   
    try:
        stdout, stderr = run_job(full_cmd.strip(), 
                                 job_other_options=job_options,
                                 run_locally = run_locally, 
                                 retain_job_scripts = retain_job_scripts, job_script_directory = job_script_dir,
                                 logger=logger, working_directory=os.getcwd(),
                                 drmaa_session = drmaa_session)
    except error_drmaa_job as err:
        raise Exception("\n".join(map(str, ["Failed to run:", cmd, err, stdout, stderr])))


""" 
Currently not available in dockerized mode. 
Only default job scheduling params of run_command available when executing via SLURM.
"""
def run_piped_command(*args):
    run_locally=True
    retain_job_scripts = True
    job_script_dir = os.path.join(runs_scratch_dir, "drmaa")	
    cpus=1
    mem_per_cpu=1024
    walltime="24:00:00"
 
    stdout, stderr = "", ""
    job_options = "--ntasks=1 \
                   --cpus-per-task={cpus} \
                   --mem-per-cpu={mem} \
                   --time={time} \
                  ".format(cpus=cpus, mem=int(1.2*mem_per_cpu), time=walltime)
	
    full_cmd = expand_piped_command(*args)
	
    try:
        stdout, stderr = run_job(full_cmd.strip(), 
                                 job_other_options=job_options,
                                 run_locally = run_locally, 
                                 retain_job_scripts = retain_job_scripts, job_script_directory = job_script_dir,
                                 logger=logger, working_directory=os.getcwd(),
                                 drmaa_session = drmaa_session)
    except error_drmaa_job as err:
        raise Exception("\n".join(map(str, ["Failed to run:", full_cmd, err, stdout, stderr])))
	
def expand_piped_command(cmd, cmd_args, interpreter_args=None, *args):
	expanded_cmd = cmd.format(args=cmd_args, interpreter_args = interpreter_args if interpreter_args!=None else "")
	expanded_cmd += (" | "+expand_piped_command(*args)) if len(args) > 0 else ""
	return expanded_cmd


def produce_fastqc_report(fastq_file, output_dir=None):
    args = fastq_file
    args += (' -o '+output_dir) if output_dir != None else ''
    run_cmd(fastqc, args, dockerize=dockerize)



    


#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888

#   Pipeline


#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888

from ruffus import *


#
#
# Prepare FASTQ
# 

@active_if(run_folder != None)
@follows(mkdir(runs_scratch_dir), mkdir(os.path.join(runs_scratch_dir,'fastqs')))
@files(run_folder, os.path.join(runs_scratch_dir,'fastqs','completed'))
@posttask(touch_file(os.path.join(runs_scratch_dir,'fastqs','completed')))
def bcl2fastq_conversion(run_directory, completed_flag):
    """ Run bcl2fastq conversion and create fastq files in the run directory"""
    out_dir = os.path.join(runs_scratch_dir,'fastqs')
    interop_dir = os.path.join(out_dir,'InterOp')

    # r, w, d, and p specify numbers of threads to be used for each of the concurrent subtasks of the conversion (see bcl2fastq manual) 
    args = "-R {indir} -o {outdir} --interop-dir={interopdir} -r1 -w1 -d2 -p4 \
            ".format(indir=run_directory, outdir=out_dir, interopdir=interop_dir)
    if options.run_on_bcl_tile != None:
        args += " --tiles %s" % options.run_on_bcl_tile
        
    run_cmd(bcl2fastq, args, dockerize=dockerize, cpus=8, mem_per_cpu=2048)
    


@active_if(run_folder != None and fastq_archive != None)
@transform(bcl2fastq_conversion, formatter(".+/(?P<RUN_ID>[^/]+)/fastqs/completed"), str(fastq_archive)+"/{RUN_ID[0]}")
def archive_fastqs(completed_flag, archive_dir):
    """ Archive fastqs """    
    fq_dir = os.path.dirname(completed_flag)

# uncomment if archive should not be overwritten (risk of creating many archives of the same run)
#    if os.path.exists(archive_dir):
#	import time
#	archive_dir += "_archived_"+str(time.strftime("%Y%m%d_%H%M%S"))

    import shutil
    shutil.move(fq_dir, archive_dir)
    os.mkdir(fq_dir)
    for f in glob.glob(os.path.join(archive_dir,"*.fastq.gz")):
        os.symlink(f, os.path.join(fq_dir,os.path.basename(f)))


#
# Prepare directory for every sample and link the input fastq files
# Expected format:
#    /path/to/file/[SAMPLE_ID]_S[1-9]\d?_L\d\d\d_R[12]_001.fastq.gz
# SAMPLE_ID can contain all signs except path delimiter, i.e. "\"
#
@active_if(run_folder != None or input_fastqs != None)
@jobs_limit(1)    # to avoid problems with simultanous creation of the same sample dir
@follows(archive_fastqs)
@transform(os.path.join(runs_scratch_dir,'fastqs','*.fastq.gz') if run_folder != None else input_fastqs,
           formatter('(?P<PATH>.+)/(?P<SAMPLE_ID>[^/]+)_S[1-9]\d?_L\d\d\d_R[12]_001\.fastq\.gz$'), 
           runs_scratch_dir+'/{SAMPLE_ID[0]}/{basename[0]}{ext[0]}')
def link_fastqs(fastq_in, fastq_out):
    """Make working directory for every sample and link fastq files in"""
    if not os.path.exists(os.path.dirname(fastq_out)):
        os.mkdir(os.path.dirname(fastq_out))
    if not os.path.exists(fastq_out):
        os.symlink(fastq_in, fastq_out) 

    
    
    
    #8888888888888888888888888888888888888888888888888888
    #
    #                T r i m m i n g  
    #
    #8888888888888888888888888888888888888888888888888888
    
    

#
# Input FASTQ filenames are expected to have following format:
#    [SAMPLE_ID]_[S_NUM]_[LANE_ID]_[R1|R2]_001.fastq.gz
# In this step, the two FASTQ files matching on the [SAMPLE_ID]_[S_ID]_[LANE_ID] will be trimmed together (R1 and R2). 
# The output will be written to two FASTQ files
#    [SAMPLE_ID]_[LANE_ID].fq1.gz
#    [SAMPLE_ID]_[LANE_ID].fq2.gz
# SAMPLE_ID can contain all signs except path delimiter, i.e. "\"
#
@active_if(run_folder != None or input_fastqs != None)
@collate(link_fastqs, regex(r'(.+)/([^/]+)_S[1-9]\d?_(L\d\d\d)_R[12]_001\.fastq\.gz$'), 
                      [r'\1/\2_R1.fq.gz', r'\1/\2_R2.fq.gz', r'\1/\2_R1_unpaired.fq.gz', r'\1/\2_R2_unpaired.fq.gz'])
def trim_reads(inputs, outfqs):
    """ Trim reads """
    args = "PE -phred33 -threads 1 \
            {in1} {in2} {out1} {unpaired1} {out2} {unpaired2} \
            ILLUMINACLIP:{adapter}:2:30:10 \
            SLIDINGWINDOW:4:15 MINLEN:36 \
            ".format(in1=inputs[0], in2=inputs[1],
                                       out1=outfqs[0], out2=outfqs[1],
                                       unpaired1=outfqs[2], unpaired2=outfqs[3],
                                       adapter=adapters)
#    max_mem = 2048
    run_cmd(trimmomatic, args, #interpreter_args="-Xmx"+str(max_mem)+"m", 
            dockerize=dockerize)#, cpus=1, mem_per_cpu=max_mem)
    
    
        
    #8888888888888888888888888888888888888888888888888888
    #
    #        M e r g i n g   &   t r i m m i n g   
    #
    #8888888888888888888888888888888888888888888888888888

    
    
#
# Input FASTQ filenames are expected to have following format:
#    [SAMPLE_ID]_[S_NUM]_[LANE_ID]_[R1|R2]_001.fastq.gz
# In this step, overlapping reads from two FASTQ files matching on [SAMPLE_ID] will be merged together. 
# The output will be written to three FASTQ files
#    [SAMPLE_ID]_merged.fq.gz - containing merged reads
#    [SAMPLE_ID]_R1.fq.gz     - with notmerged R1
#    [SAMPLE_ID]_R2.fq.gz     - with notmerged R2 
# SAMPLE_ID can contain all signs except path delimiter, i.e. "\"
# 
@active_if(run_folder != None or input_fastqs != None)
@collate(link_fastqs, regex(r'(.+)/([^/]+)_S[1-9]\d?_(L\d\d\d)_R[12]_001\.fastq\.gz$'), [r'\1/\2_merged.fq.gz', r'\1/\2_notmerged_R1.fq.gz', r'\1/\2_notmerged_R2.fq.gz'])
def merge_reads(inputs, outputs):
	""" Merge overlapping reads """
	
	hist=outputs[0].replace('_merged.fq.gz','.hist')
	args='in1={fq1} in2={fq2} \
		  out={fqm} outu1={u1} outu2={u2} \
		  ihist={hist} adapters={adapters} \
		  '.format(fq1=inputs[0], fq2=inputs[1],
					fqm=outputs[0], u1=outputs[1], u2=outputs[2],
					hist=hist, adapters=adapters)
		  
	run_cmd(bbmerge, args, dockerize=dockerize)
    
    
    
#
# Input FASTQ filenames are expected to have following format:
#    [SAMPLE_ID]_merged.fq.gz and [SAMPLE_ID]_R[12].fq.gz
# In this task, merged reads will be trimmed in one step, and next the 
# two FASTQ files with nonoverlapping R1 and R2 reads will be trimmed together. 
# The output will be written to five FASTQ files
#	 [SAMPLE_ID]_merged.trimmed.fq.gz
#    [SAMPLE_ID]_R1.trimmed.fq.gz
#    [SAMPLE_ID]_R1.unpaired.fq.gz
#    [SAMPLE_ID]_R2.trimmed.fq.gz
#    [SAMPLE_ID]_R2.unpaired.fq.gz
#
# SAMPLE_ID can contain all signs except path delimiter, i.e. "\"
#
@active_if(run_folder != None or input_fastqs != None)
@transform(merge_reads, formatter('(.+)/(?P<S>[^/]+)_merged\.fq\.gz$', 
								  '(.+)/(?P<S>[^/]+)_R1\.fq\.gz$', 
								  '(.+)/(?P<S>[^/]+)_R2\.fq\.gz$'), 
						['{path[0]}/{S[0]}_merged.trimmed.fq.gz',
						'{path[0]}/{S[1]}_R1.trimmed.fq.gz',  '{path[0]}/{S[2]}_R2.trimmed.fq.gz',
						'{path[0]}/{S[1]}_R1.unpaired.fq.gz', '{path[0]}/{S[2]}_R2.unpaired.fq.gz',])
def trim_merged_reads(inputs, outfqs):
    """ Trim merged and nonoverlapping read pairs """

    args1 = "SE -phred33 -threads 1 \
            {fq_in} {fq_out} ILLUMINACLIP:{adapter}:2:30:10 \
            SLIDINGWINDOW:4:15 MINLEN:36 \
            ".format(fq_in=inputs[0], fq_out=outfqs[0], adapter=adapters)
    run_cmd(trimmomatic, args1, dockerize=dockerize)
    
    
    args2 = "PE -phred33 -threads 1 \
            {in1} {in2} {out1} {unpaired1} {out2} {unpaired2} \
            ILLUMINACLIP:{adapter}:2:30:10 \
            SLIDINGWINDOW:4:15 MINLEN:36 \
            ".format(in1=inputs[1], in2=inputs[2],
                     out1=outfqs[1], out2=outfqs[2],
                     unpaired1=outfqs[3], unpaired2=outfqs[4],
                     adapter=adapters)
    run_cmd(trimmomatic, args2, dockerize=dockerize)




    #8888888888888888888888888888888888888888888888888888
    #
    #              F i l t e r i n g 
    #
    #8888888888888888888888888888888888888888888888888888



def filter_reads_by_mapping(in_fqs, out_fqs, reference, remove_matching=True):
	""" 
	Filters reads by removing / keeping those matchin the reference genome. 
	The genome must be BWA indexed first 
	"""
	
#	cmd="bwa mem -t {threads} {ref} {fq1} {fq2} | \
#	     samtools view -S -b -{flag} 4 | \
#	     bedtools bamtofastq -i /dev/stdin -fq {out1} \
#	     ".format(threads=threads, ref=genome,
#				fq1=in_fqs[0], fq2=(in_fqs[1] if len(in_fqs)>1 else ""),
#				flag=("f" if remove_matching else "F"))
        threads=2
	
	bwa_args = "mem -t {threads} {ref} ".format(threads=threads, ref=reference)
	if isinstance(in_fqs, str):
		bwa_args += in_fqs
	else:
		bwa_args += "%s %s" % (in_fqs[0], in_fqs[1])

	samtools_args = "view -S -b -{flag} 4 ".format(flag=("f" if remove_matching else "F"))

	bedtools_args = "bamtofastq -i /dev/stdin "
	if isinstance(out_fqs, str) and isinstance(in_fqs, str):
		bedtools_args += "-fq %s" % out_fqs
	else:
		bedtools_args += "-fq {out1} -fq2 {out2}".format(out1=out_fqs[0], out2=out_fqs[1])

	run_piped_command(bwa, bwa_args, None,
	                  samtools, samtools_args, None,
			  bedtools, bedtools_args, None)
					

@transform(trim_merged_reads, 
			formatter('(.+)/(?P<S>[^/]+)_merged\.trimmed\.fq\.gz$',
					  '(.+)/(?P<S>[^/]+)_R1\.trimmed\.fq\.gz$', 
                      '(.+)/(?P<S>[^/]+)_R2\.trimmed\.fq\.gz$', 
                      '(.+)/(?P<S>[^/]+)_R1\.unpaired\.fq\.gz$',
                      '(.+)/(?P<S>[^/]+)_R2\.unpaired\.fq\.gz$'),
            ['{path[0]}/{S[0]}_merged.trimmed.host_filtered.fq',
             '{path[0]}/{S[1]}_R1.trimmed.host_filtered.fq',  
             '{path[0]}/{S[2]}_R2.trimmed.host_filtered.fq',  
             '{path[0]}/{S[3]}_R1.unpaired.host_filtered.fq', 
             '{path[0]}/{S[4]}_R2.unpaired.host_filtered.fq'])
def filter_host_genome_from_merged(in_fqs, out_fqs):
	""" Filter reads matching the host genome """
	filter_reads_by_mapping(in_fqs[0], out_fqs[0], host_genome)
	filter_reads_by_mapping(in_fqs[1:3], out_fqs[1:3], host_genome)
	filter_reads_by_mapping(in_fqs[3], out_fqs[3], host_genome)
	filter_reads_by_mapping(in_fqs[4], out_fqs[4], host_genome)


def bbduk_filter(ref_db, in_fq, out_unmatched, out_matched,
                 in_fq2=None, out_unmatched2=None, out_matched2=None):
    """ Filter reads by kmer similarity """

    args = "in={fqm} out={out_fq} outm={out_fq_matched} \
            ref={db} stats={stats} k=31 hdist=0 overwrite=t -Xmx8g \
            ".format(fqm=in_fq, out_fq=out_unmatched, out_fq_matched=out_matched, 
                    db=ref_db, stats=out_matched+".stats")

    if in_fq2 != None:
        args += " in2={fq2} out2={out2} outm2={outm2} \
                ".format(fq2=in_fq2, out2=out_unmatched2, outm2=out_matched2)

    run_cmd(bbduk, args, dockerize=dockerize, cpus=1, mem_per_cpu=8192)


@transform(trim_reads, 
            formatter('(.+)/(?P<S>[^/]+)_R1\.fq\.gz$', 
                      '(.+)/(?P<S>[^/]+)_R2\.fq\.gz$', 
                      '(.+)/(?P<S>[^/]+)_R1_unpaired\.fq\.gz$',
                      '(.+)/(?P<S>[^/]+)_R2_unpaired\.fq\.gz$'),
            ['{path[0]}/{S[0]}_R1.filtered.fq.gz',  
             '{path[0]}/{S[1]}_R2.filtered.fq.gz',  
             '{path[0]}/{S[2]}_R1_unpaired.filtered.fq.gz', 
             '{path[0]}/{S[3]}_R2_unpaired.filtered.fq.gz'],
            ['{path[0]}/{S[0]}_R1.matchedSILVA.fq.gz', 
             '{path[0]}/{S[1]}_R2.matchedSILVA.fq.gz',
             '{path[0]}/{S[2]}_R1_unpaired.matchedSILVA.fq.gz',
             '{path[0]}/{S[3]}_R2_unpaired.matchedSILVA.fq.gz'])
def filter_riborna_from_trimmed(input_fqs, filtered_outs, matched_outs):
    """ Filter rRNA from trimmed reads files """
    # filter paired 
    bbduk_filter(silva_database, 
                 input_fqs[0], filtered_outs[0], matched_outs[0], 
                 input_fqs[1], filtered_outs[1], matched_outs[1])
    # filter unpaired
    bbduk_filter(silva_database, input_fqs[2], filtered_outs[2], matched_outs[2])
    bbduk_filter(silva_database, input_fqs[3], filtered_outs[3], matched_outs[3])


@transform(trim_merged_reads, 
            formatter('(.+)/(?P<S>[^/]+)_merged\.trimmed\.fq\.gz$',
					  '(.+)/(?P<S>[^/]+)_R1\.trimmed\.fq\.gz$', 
                      '(.+)/(?P<S>[^/]+)_R2\.trimmed\.fq\.gz$', 
                      '(.+)/(?P<S>[^/]+)_R1\.unpaired\.fq\.gz$',
                      '(.+)/(?P<S>[^/]+)_R2\.unpaired\.fq\.gz$'),
            ['{path[0]}/{S[0]}_merged.trimmed.filtered.fq.gz',
             '{path[0]}/{S[1]}_R1.trimmed.filtered.fq.gz',  
             '{path[0]}/{S[2]}_R2.trimmed.filtered.fq.gz',  
             '{path[0]}/{S[3]}_R1.unpaired.filtered.fq.gz', 
             '{path[0]}/{S[4]}_R2.unpaired.filtered.fq.gz'],
            ['{path[0]}/{S[0]}_merged.trimmed.matchedSILVA.fq.gz',
             '{path[0]}/{S[1]}_R1.trimmed.matchedSILVA.fq.gz', 
             '{path[0]}/{S[2]}_R2.trimmed.matchedSILVA.fq.gz',
             '{path[0]}/{S[3]}_R1.unpaired.matchedSILVA.fq.gz',
             '{path[0]}/{S[4]}_R2.unpaired.matchedSILVA.fq.gz'])
def filter_riborna_from_merged(input_fqs, filtered_outs, matched_outs):
    """ Filter rRNA from merged trimmed reads, and from not merged read pairs """
    # filter merged
    bbduk_filter(silva_database, input_fqs[0], filtered_outs[0], matched_outs[0])
    
    # filter paired 
    bbduk_filter(silva_database, 
                 input_fqs[1], filtered_outs[1], matched_outs[1], 
                 input_fqs[2], filtered_outs[2], matched_outs[2])
                 
    # filter unpaired
    bbduk_filter(silva_database, input_fqs[3], filtered_outs[3], matched_outs[3])
    bbduk_filter(silva_database, input_fqs[4], filtered_outs[4], matched_outs[4])





    #8888888888888888888888888888888888888888888888888888
    #
    #                   M a p p i n g 
    #
    #8888888888888888888888888888888888888888888888888888




def bwa_map_and_sort(output_bam, ref_genome, fq1, fq2=None, threads=1):
	bwa_args = "mem -t {threads} {ref} {fq1} \
	           ".format(threads=threads, ref=ref_genome, fq1=fq1)
	if fq2 != None:
		bwa_args += fq2

	samtools_args = "sort -o {out}".format(out=output_bam)

	run_piped_command(bwa, bwa_args, None,
	                  samtools, samtools_args, None)

def merge_bams(out_bam, *in_bams):
	threads = 1
	mem = 4096
	
	args = "merge %s" % out_bam
	for bam in in_bams:
		args += (" "+bam)
		
	run_cmd(samtools, args, dockerize=dockerize, cpus=threads, mem_per_cpu=int(mem/threads))
	
	
def map_reads(fastq_list, ref_genome, output_bam):
    
    tmp_bams = [ output_bam+str(i) for i in range(0, len(fastq_list)) ]
    for i in range(0, len(fastq_list)):
		if isinstance(fastq_list[i], tuple):
			bwa_map_and_sort(tmp_bams[i], ref_genome, fastq_list[i][0], fastq_list[i][1])
		else:
			bwa_map_and_sort(tmp_bams[i], ref_genome, fastq_list[i])   
    
    merge_bams(output_bam, *tmp_bams)
    
    for f in tmp_bams:
		  os.remove(f)

@jobs_limit(1)
@transform(trim_merged_reads, formatter(), "{subpath[0][0]}/{subdir[0][0]}_notfiltered.bam")
def map_trimmed_merged_reads(fastqs, bam_file):
    """ Maps host-filtered reads from merging path. Both merged pairs and not-merged, paired and unpaired R1 are included """
    fqm=fastqs[0]
    fq1=fastqs[1]
    fq2=fastqs[2]
    fq1u=fastqs[3]
    # fq2u is typicaly small and low quality

    map_reads([fqm, (fq1,fq2), fq1u], reference, bam_file)


@jobs_limit(1)
@transform(filter_host_genome_from_merged, formatter(), "{subpath[0][0]}/{subdir[0][0]}.bam")
def map_host_filtered_merged_reads(fastqs, bam_file):
    """ Maps host-filtered reads from merging path. Both merged pairs and not-merged, paired and unpaired R1 are included """
    fqm=fastqs[0]
    fq1=fastqs[1]
    fq2=fastqs[2]
    fq1u=fastqs[3]
    # fq2u is typicaly small and low quality

    map_reads([fqm, (fq1,fq2), fq1u], reference, bam_file)

@jobs_limit(1)
@transform(filter_riborna_from_merged, formatter(), "{subpath[0][0]}/{subdir[0][0]}.bam")
def map_ribo_filtered_merged_reads(fastqs, bam_file):
    """ Maps ribo-filtered reads from merging path. Both merged pairs and not-merged, paired and unpaired R1 are included """
    fqm=fastqs[0]
    fq1=fastqs[1]
    fq2=fastqs[2]
    fq1u=fastqs[3]
    # fq2u is typicaly small and low quality

    map_reads([fqm, (fq1,fq2), fqu1], reference, bam_file)






    #8888888888888888888888888888888888888888888888888888
    #
    #         V a r i a n t   c a l l i n g
    #
    #8888888888888888888888888888888888888888888888888888



def call_variants_lofreq(bam, vcf, ref_genome):
    
    threads = 1
    mem = 4096
    args = "call -f {ref} -o {vcf} {bam} \
           ".format(ref=ref_genome, vcf=vcf, bam=bam)
    run_cmd(lofreq, args, dockerize=dockerize, cpus=threads, mem_per_cpu=int(mem/threads))


@transform(map_ribo_filtered_merged_reads, suffix(".bam"), ".lofreq.vcf")
def call_variants_on_host_filtered(bam, vcf):
	""" Call variants using lofreq* on host filtered mapped reads """
	call_variants_lofreq(bam, vcf, reference)




    #8888888888888888888888888888888888888888888888888888
    #
    #                  A s s e m b l y
    #
    #8888888888888888888888888888888888888888888888888888



def clean_trimmed_fastqs():
    """ Remove the trimmed fastq files. Links to original fastqs are kept """
    for f in glob.glob(os.path.join(runs_scratch_dir,'*','*.fq.gz')):
        os.remove(f)

def clean_spades_workdir():
    import shutil
    """ Remove the trimmed fastq files. Links to original fastqs are kept """
    for f in glob.glob(os.path.join(runs_scratch_dir,'*','*assembly')):
        if os.path.isdir(f):
            shutil.rmtree(f, ignore_errors=True)

#
# FASTQ filenames are expected to have following format:
#    [SAMPLE_ID]_merged.trimmed.gz
#    [SAMPLE_ID]_R[12].trimmed.gz
#    [SAMPLE_ID]_R[12].unpaired.gz
# In this step, the FASTQ files coming from trim_merged_reads and trim_paired_reads are matched, and assembled together. 
# The output will be written to SAMPLE_ID directory:
#    [SAMPLE_ID]/
#

def run_spades(out_dir, fq=None, fq1=None, fq2=None, 
					fq1_single=None, fq2_single=None, 
					threads = 4, mem=8192):
						
    args = "-o {out_dir} -m {mem} -t {threads} --careful ".format(out_dir=out_dir, mem=mem, threads=threads)
	
	# PE inputs if provided
    if fq1 != None and fq2 != None: 
        args += " --pe1-1 {fq1} --pe1-2 {fq2}".format(fq1=fq1,fq2=fq2)
		
	# add SE inputs
    i = 1
    for se_input in [fq, fq1_single, fq2_single]:
        if se_input != None:
            args += " --s{index} {se_input}".format(index=i, se_input=se_input)
            i = i + 1
	
    print args
    run_cmd(spades, args, dockerize=dockerize, cpus=threads, mem_per_cpu=int(mem/threads))

def spades_assembly(scaffolds_file, **args):
    
    out_dir=os.path.join(os.path.dirname(scaffolds_file), 'assembly_tmp')
    if not os.path.isdir(out_dir):
		os.mkdir(out_dir)
        
    run_spades(out_dir, **args)
    
    import shutil
    shutil.copy(os.path.join(out_dir,'scaffolds.fasta'), scaffolds_file)
    shutil.copy(os.path.join(out_dir,'contigs.fasta'),   scaffolds_file+'.contigs.fasta')
    shutil.rmtree(out_dir)


@jobs_limit(1)
#@posttask(clean_trimmed_fastqs)
@transform(trim_merged_reads, formatter(), '{subpath[0][0]}/{subdir[0][0]}_mr.fasta')
def assemble_all_reads(fastqs, scaffolds):
    """ Assembles not-filtered reads from merged path, both merged pairs and notmerged are included """
    fqm=fastqs[0]
    fq1=fastqs[1]
    fq2=fastqs[2]
    fq1u=fastqs[3]
    # fq2u is typicaly low quality
    spades_assembly(scaffolds, fq=fqm, fq1=fq1, fq2=fq2, fq1_single=fq1u)


@jobs_limit(1)
@transform(filter_host_genome_from_merged, formatter(), '{subpath[0][0]}/{subdir[0][0]}_hfmr.fasta')
def assemble_host_filtered_merged_reads(fastqs, scaffolds):
    fqm=fastqs[0]
    fq1=fastqs[1]
    fq2=fastqs[2]
    fq1u=fastqs[3]
    # fq2u is typicaly small and low quality
    spades_assembly(scaffolds, fq=fqm, fq1=fq1, fq2=fq2, fq1_single=fq1u)


@jobs_limit(1)
#@posttask(clean_trimmed_fastqs)
@transform(filter_riborna_from_trimmed, formatter(), '{subpath[0][0]}/{subdir[0][0]}_ftr.fasta')
def assemble_trimmed_filtered_reads(fastqs, scaffolds):
    """ Assembles filtered reads from no-merge path, both paired and unpaired R1 are included """
    fq1=fastqs[0]
    fq2=fastqs[1]
    fq1u=fastqs[2]
    # fqu2 is typicaly small and low quality
    #fq2u=fastqs[3]
    spades_assembly(scaffolds, fq1=fq1, fq2=fq2, fq1_single=fq1u)

      
@jobs_limit(1)
#@posttask(clean_trimmed_fastqs)
@transform(filter_riborna_from_merged, formatter(), '{subpath[0][0]}/{subdir[0][0]}_fmro.fasta')      
def assemble_filtered_merged_only_reads(fastqs, scaffolds):
    """ Assembles filtered reads from merging path, only merged reads are used """
    spades_assembly(scaffolds, fq=fastqs[0])


@jobs_limit(1)
#@posttask(clean_trimmed_fastqs)
@transform(filter_riborna_from_merged, formatter(), '{subpath[0][0]}/{subdir[0][0]}_fmr.fasta')      
def assemble_filtered_merged_reads(fastqs, scaffolds):
    """ Assembles filtered reads from merging path, both merged pairs and not-merged, paired and unpaired R1 are included """
    fqm=fastqs[0]
    fq1=fastqs[1]
    fq2=fastqs[2]
    fq1u=fastqs[3]
    # fq2u is typicaly small and low quality
    spades_assembly(scaffolds, fq=fqm, fq1=fq1, fq2=fq2, fq1_single=fq1u)


#
#
# QC the FASTQ files
#

@follows(mkdir(os.path.join(runs_scratch_dir,'qc')), mkdir(os.path.join(runs_scratch_dir,'qc','read_qc')))
@transform(link_fastqs, formatter('.+/(?P<SAMPLE_ID>[^/]+)\.fastq\.gz$'), 
           os.path.join(runs_scratch_dir,'qc','read_qc/')+'{SAMPLE_ID[0]}_fastqc.html')
def qc_raw_reads(input_fastq, report):
    """ Generate FastQC report for raw FASTQs """
    produce_fastqc_report(input_fastq, os.path.dirname(report))


@follows(mkdir(os.path.join(runs_scratch_dir,'qc')), mkdir(os.path.join(runs_scratch_dir,'qc','read_qc')))
@transform(trim_reads, formatter('.+/(?P<SAMPLE_ID>[^/]+)\.fq\.gz$', '.+/(?P<SAMPLE_ID>[^/]+)\.fq\.gz$'), 
           [os.path.join(runs_scratch_dir,'qc','read_qc/')+'{SAMPLE_ID[0]}.fq_fastqc.html',
            os.path.join(runs_scratch_dir,'qc','read_qc/')+'{SAMPLE_ID[1]}.fq_fastqc.html'])
def qc_trimmed_reads(input_fastqs, reports):
    """ Generate FastQC report for trimmed PE FASTQs """
    produce_fastqc_report(input_fastqs[0], os.path.dirname(reports[0]))
    produce_fastqc_report(input_fastqs[1], os.path.dirname(reports[1]))


@follows(mkdir(os.path.join(runs_scratch_dir,'qc')), mkdir(os.path.join(runs_scratch_dir,'qc','read_qc')))
@transform(trim_merged_reads, 
		formatter('.+/(?P<SAMPLE_ID>[^/]+)_merged.trimmed\.fq\.gz$',
				'.+/(?P<SAMPLE_ID>[^/]+)_R1.trimmed\.fq\.gz$',
				'.+/(?P<SAMPLE_ID>[^/]+)_R2.trimmed\.fq\.gz$',
				'.+/(?P<SAMPLE_ID>[^/]+)_R1.unpaired\.fq\.gz$',
				'.+/(?P<SAMPLE_ID>[^/]+)_R2.unpaired\.fq\.gz$'), 
		[os.path.join(runs_scratch_dir,'qc','read_qc')+'/{SAMPLE_ID[0]}_merged.trimmed.fastqc.html',
		os.path.join(runs_scratch_dir,'qc','read_qc')+'/{SAMPLE_ID[1]}_R1.trimmed.fastqc.html',
		os.path.join(runs_scratch_dir,'qc','read_qc')+'/{SAMPLE_ID[2]}_R2.trimmed.fastqc.html',
		os.path.join(runs_scratch_dir,'qc','read_qc')+'/{SAMPLE_ID[3]}_R1.unpaired.fastqc.html',
		os.path.join(runs_scratch_dir,'qc','read_qc')+'/{SAMPLE_ID[4]}_R2.unpaired.fastqc.html'])
def qc_merged_reads(input_fastqs, reports):
    """ Generate FastQC report for trimmed FASTQs """
    for i in range(0,len(input_fastqs)):
		produce_fastqc_report(input_fastqs[i], os.path.dirname(reports[i]))

    
def count_reads(fastq):
    import gzip
    with ( gzip.open(fastq) if fastq[-3:] == '.gz' else open(fastq) ) as f:
        for i, l in enumerate(f, 1): 
            pass   
    return i/4

def count_reads_and_basepairs(fastq):
    """ returns a tuple (#bps, #reads) """
    import gzip
    
    bps=0
    with ( gzip.open(fastq) if fastq[-3:] == '.gz' else open(fastq) ) as f:
        for i, l in enumerate(f,1): 
            if i % 4 == 2:  # read sequence is in 2nd line of each four
                bps += len(l.strip())
                
    return (bps, i/4)


@collate([link_fastqs, filter_host_genome_from_merged, trim_merged_reads], 
        regex(r'.+/(.+)/.+'), 
        os.path.join(runs_scratch_dir,'qc','read_qc')+r'/\1.read_stats.tsv')
def qc_host_filtering_stats(inputs, output):
    """
    Gather read and bp stats to make a tab separated table
    """
    
    # ===============================================================
    # SAMPLE | CATEGORY |    RAW      | MERGED/TRIMMED |  FILTERED 
    #        |          | [bps|reads] |   [bps|reads]  | [bps|reads]
    # ===============================================================
    #        | MERGED   |             |                |
    #        | PAIRED   |             |                |
    #        | UNPAIRED |             |                |
    #        | ALL      |             |                |
    # ===============================================================

    raw = inputs[0], inputs[1]
    trimmed = inputs[2]
    filtered = inputs[3]
       
    stats={}
    stats['mr']  = (0,0) + \
                   count_reads_and_basepairs(trimmed[0]) + \
                   count_reads_and_basepairs(filtered[0])
    
    stats['prd'] = [sum(e) for e in zip(count_reads_and_basepairs(raw[0]), count_reads_and_basepairs(raw[1]))] + \
                   [sum(e) for e in zip(count_reads_and_basepairs(trimmed[1]), count_reads_and_basepairs(trimmed[2]))] + \
                   [sum(e) for e in zip(count_reads_and_basepairs(filtered[1]), count_reads_and_basepairs(filtered[2]))]
                   
    stats['unp'] = [0,0] + \
                   [sum(e) for e in zip(count_reads_and_basepairs(trimmed[3]), count_reads_and_basepairs(trimmed[4]))] + \
                   [sum(e) for e in zip(count_reads_and_basepairs(filtered[3]), count_reads_and_basepairs(filtered[4]))]
                   
    stats['all'] = [sum(e) for e in zip(stats['mr'], stats['prd'], stats['unp'])] 
    
    mrl  = 'merged\t'   + '\t'.join([str(e) for e in stats['mr']])
    prdl = 'paired\t'   + '\t'.join([str(e) for e in stats['prd']])
    unpl = 'unpaired\t' + '\t'.join([str(e) for e in stats['unp']])
    alll = 'all\t'      + '\t'.join([str(e) for e in stats['all']])
    
    header = '\t'.join(['sample','read_category',
                        'raw_bps', 'raw_reads',
                        'trimmed_bps','trimmed_reads',
                        'filtered_bps','filtered_reads'])
    sample = os.path.basename(trimmed[0])[:-len('_merged.trimmed.fq.gz')]
    
    with open(output, 'w') as statf:
        statf.write(('\n'+sample+'\t').join([header, mrl, prdl, unpl, alll]))
    




@follows(qc_raw_reads, qc_merged_reads)
def qc_reads():
    pass

#
#
# QC the assemblies
#

@follows(mkdir(os.path.join(runs_scratch_dir,'qc')), mkdir(os.path.join(runs_scratch_dir,'qc','assembly_qc')))
@merge(assemble_all_reads, os.path.join(runs_scratch_dir, 'qc', 'assembly_qc','quast_report'))
def qc_assemblies(scaffolds, report_dir):
    args = ("-o %s " % report_dir) + " ".join(scaffolds)
    run_cmd(quast, args, dockerize=dockerize)

@follows(mkdir(os.path.join(runs_scratch_dir,'qc')), mkdir(os.path.join(runs_scratch_dir,'qc','assembly_qc')))
@merge(assemble_filtered_merged_reads, os.path.join(runs_scratch_dir, 'qc', 'assembly_qc','quast_report'))
def qc_assemblies2(scaffolds, report_dir):
    args = ("-o %s " % report_dir) + " ".join(scaffolds)
    run_cmd(quast, args, dockerize=dockerize)



#def archive_results():
    ## if optional results_archive was not provided - do nothing
    #if results_archive == None: return
    #arch_path = os.path.join(results_archive, run_id)
    #if not os.path.exists(arch_path): 
        #os.mkdir(arch_path)
        
    #run_cmd("cp %s/*/*.gatk.bam %s" % (runs_scratch_dir,arch_path), "", run_locally=True)
    #run_cmd("cp %s/*/*.gatk.bam.gene_coverage* %s" % (runs_scratch_dir,arch_path), "", run_locally=True)
    #run_cmd("cp %s/*/*.exome.vcf %s" % (runs_scratch_dir,arch_path), "", run_locally=True)
    #run_cmd("cp %s/*.multisample.gvcf %s" % (runs_scratch_dir, results_archive),
            #"", run_locally=True)
    #run_cmd("cp -r %s/qc %s" % (runs_scratch_dir,arch_path), "", run_locally=True)


#def cleanup_files():
    #run_cmd("rm -rf {dir}/*/*.recal_data.csv {dir}/*/*.realign* {dir}/*/*.dedup* \
            #{dir}/*.multisample.indel.model* {dir}/*.multisample.snp.model* \
            #{dir}/*/*.log {dir}/*.multisample.recalibratedSNPS.rawIndels.vcf* \
            #{dir}/*.multisample.recalibrated.vcf* \
            #".format(dir=runs_scratch_dir), "", run_locally=True)


#@posttask(archive_results, cleanup_files)
@follows(qc_reads, qc_assemblies)
def complete_run():
    pass





#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888

#   Main logic


#88888888888888888888888888888888888888888888888888888888888888888888888888888888888888888
if __name__ == '__main__':
    if options.just_print:
        pipeline_printout(sys.stdout, options.target_tasks, options.forced_tasks,
                            gnu_make_maximal_rebuild_mode = options.rebuild_mode,
                            verbose=options.verbose, #verbose_abbreviated_path=0,
                            checksum_level = 0)

    elif options.flowchart:
        pipeline_printout_graph (   open(options.flowchart, "w"),
                                    # use flowchart file name extension to decide flowchart format
                                    #   e.g. svg, jpg etc.
                                    os.path.splitext(options.flowchart)[1][1:],
                                    options.target_tasks,
                                    options.forced_tasks,
                                        gnu_make_maximal_rebuild_mode = options.rebuild_mode,
                                    no_key_legend   = not options.key_legend_in_graph)
    else:        
        pipeline_run(options.target_tasks, options.forced_tasks,
                            multithread     = options.jobs,
                            logger          = stderr_logger,
                            verbose         = options.verbose,
                            gnu_make_maximal_rebuild_mode = options.rebuild_mode,
                            checksum_level  = 0)
    
        
    drmaa_session.exit()
    
