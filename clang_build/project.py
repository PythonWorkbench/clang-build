'''
Target describes a single build or dependency target with all needed paths and
a list of buildables that comprise it's compile and link steps.
'''

import os as _os
import textwrap as _textwrap
import sys
from pathlib import Path as _Path
import subprocess as _subprocess
from multiprocessing import freeze_support as _freeze_support
import logging as _logging

from .dialect_check import get_max_supported_compiler_dialect as _get_max_supported_compiler_dialect
from .build_type import BuildType as _BuildType
from .target import Executable as _Executable,\
                    SharedLibrary as _SharedLibrary,\
                    StaticLibrary as _StaticLibrary,\
                    HeaderOnly as _HeaderOnly
from .dependency_tools import find_circular_dependencies as _find_circular_dependencies,\
                              find_non_existent_dependencies as _find_non_existent_dependencies,\
                              get_dependency_walk as _get_dependency_walk
from .io_tools import get_sources_and_headers as _get_sources_and_headers
from .progress_bar import CategoryProgress as _CategoryProgress,\
                          IteratorProgress as _IteratorProgress
from .logging_stream_handler import TqdmHandler as _TqdmHandler

_LOGGER = _logging.getLogger('clang_build.clang_build')



class Project:
    def __init__(self, config, environment, multiple_projects):

        self.name = config.get("name", "")

        # print(f"Project {self.name}")

        # Get subset of config which contains targets not associated to any project name
        self.targets_config = {key: val for key, val in config.items() if not key.startswith("project")}

        # Get subsets of config which define projects
        self.subprojects_config = {key: val for key, val in config.items() if key.startswith("project")}

        # An "anonymous" project, i.e. project-less targets, is not allowed together with subprojects
        if self.targets_config and self.subprojects_config:
            print(f"Project {self.name}: Your config file specified one or more projects. In this case you are not allowed to specify targets which do not belong to a project.")
            environment.logger.error(f"Project {self.name}: Your config file specified one or more projects. In this case you are not allowed to specify targets which do not belong to a project.")
            sys.exit(1)

        # Get top-level targets
        targets_config = {key: val for key, val in config.items() if not key == "subproject" and not key == "name"}

        # Get subsets of config which define projects
        subprojects_config = {key: val for key, val in config.items() if key == "subproject"}

        # print("\nProject ", self.name)
        # print("targets:     ", targets_config)
        # print("subprojects: ", subprojects_config)
        # print("full config: ", config)
    
        # An "anonymous" project, i.e. project-less targets without a project_name specified, is not allowed together with subprojects
        if (targets_config  and not self.name) and subprojects_config:
            print("On the top level, your config file specified one or more projects. In this case you are not allowed to specify targets which do not belong to a project.")
            environment.logger.error("On the top level, your config file specified one or more projects. In this case you are not allowed to specify targets which do not belong to a project.")
            sys.exit(1)

        # Generate Projects
        subprojects = []
        # if targets_config:
        #     subprojects += [Project(targets_config, environment, multiple_projects)]
        if subprojects_config:
            subprojects += [Project(config, environment, multiple_projects) for config in subprojects_config["subproject"]]

        # print(f"subprojects of {self.name}: ", [project.name if project.name else "anonymous" for project in subprojects])


        # Use sub-build directories if the project contains multiple targets
        multiple_targets = False
        if len(self.targets_config.items()) > 1:
            multiple_targets = True

        if not targets_config:
            return
        # print(targets_config)
        
        # Parse targets from toml file
        non_existent_dependencies = _find_non_existent_dependencies(targets_config)
        if non_existent_dependencies:
            error_messages = [f'In {target}: the dependency {dependency} does not point to a valid target' for\
                            target, dependency in non_existent_dependencies]

            error_message = _textwrap.indent('\n'.join(error_messages), prefix=' '*3)
            environment.logger.error(error_message)
            print(f"Project {self.name}: non_existent_dependencies.")
            sys.exit(1)

        circular_dependencies = _find_circular_dependencies(targets_config)
        if circular_dependencies:
            error_messages = [f'In {target}: circular dependency -> {dependency}' for\
                            target, dependency in non_existent_dependencies]

            error_message = _textwrap.indent('\n'.join(error_messages), prefix=' '*3)
            environment.logger.error(error_message)
            print(f"Project {self.name}: circular_dependencies.")
            sys.exit(1)


        target_names = _get_dependency_walk(targets_config)

        self.target_list = []

        # Project build directory
        self.build_directory = environment.build_directory
        if multiple_projects:
            self.build_directory = self.build_directory.joinpath(self.name)

        for target_name in _IteratorProgress(target_names, environment.progress_disabled, len(target_names)):
            project_node = targets_config[target_name]
            # Directories
            target_build_dir = self.build_directory if not multiple_targets else self.build_directory.joinpath(target_name)
            # Sources
            files = _get_sources_and_headers(project_node, environment.workingdir, target_build_dir)
            # Dependencies
            dependencies = [self.target_list[target_names.index(name)] for name in project_node.get('dependencies', [])]
            executable_dependencies = [target for target in dependencies if target.__class__ is _Executable]

            if executable_dependencies:
                environment.logger.error(f'Error: The following targets are linking dependencies but were identified as executables: {executable_dependencies}')


            if 'target_type' in project_node:
                #
                # Add an executable
                #
                if project_node['target_type'].lower() == 'executable':
                    self.target_list.append(
                        _Executable(
                            target_name,
                            environment.workingdir,
                            target_build_dir,
                            files['headers'],
                            files['include_directories'],
                            files['sourcefiles'],
                            environment.buildType,
                            environment.clangpp,
                            project_node,
                            dependencies))

                #
                # Add a shared library
                #
                if project_node['target_type'].lower() == 'shared library':
                    self.target_list.append(
                        _SharedLibrary(
                            target_name,
                            environment.workingdir,
                            target_build_dir,
                            files['headers'],
                            files['include_directories'],
                            files['sourcefiles'],
                            environment.buildType,
                            environment.clangpp,
                            project_node,
                            dependencies))

                #
                # Add a static library
                #
                elif project_node['target_type'].lower() == 'static library':
                    self.target_list.append(
                        _StaticLibrary(
                            target_name,
                            environment.workingdir,
                            target_build_dir,
                            files['headers'],
                            files['include_directories'],
                            files['sourcefiles'],
                            environment.buildType,
                            environment.clangpp,
                            environment.clang_ar,
                            project_node,
                            dependencies))

                #
                # Add a header-only
                #
                elif project_node['target_type'].lower() == 'header only':
                    if files['sourcefiles']:
                        environment.logger.info(f'Source files found for header-only target {target_name}. You may want to check your build configuration.')
                    self.target_list.append(
                        _HeaderOnly(
                            target_name,
                            environment.workingdir,
                            target_build_dir,
                            files['headers'],
                            files['include_directories'],
                            environment.buildType,
                            environment.clangpp,
                            project_node,
                            dependencies))

                else:
                    environment.logger.error(f'ERROR: Unsupported target type: {project_node["target_type"]}')

            # No target specified so must be executable or header only
            else:
                if not files['sourcefiles']:
                    environment.logger.info(f'No source files found for target {target_name}. Creating header-only target.')
                    self.target_list.append(
                        _HeaderOnly(
                            target_name,
                            environment.workingdir,
                            target_build_dir,
                            files['headers'],
                            files['include_directories'],
                            environment.buildType,
                            environment.clangpp,
                            project_node,
                            dependencies))
                else:
                    environment.logger.info(f'{len(files["sourcefiles"])} source files found for target {target_name}. Creating executable target.')
                    self.target_list.append(
                        _Executable(
                            target_name,
                            environment.workingdir,
                            target_build_dir,
                            files['headers'],
                            files['include_directories'],
                            files['sourcefiles'],
                            environment.buildType,
                            environment.clangpp,
                            project_node,
                            dependencies))

    def get_targets(self):
        return self.target_list