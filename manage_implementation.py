#!/usr/bin/env python3
"""
Implementation Plan Manager for MyProject Security

This script helps manage and track the implementation of the 10-step security plan
defined in nextGenSecurityPlanSteps.json.
"""

import json
import os
import sys
import datetime
from tabulate import tabulate
import argparse


class ImplementationManager:
    """Manages the implementation of the security plan steps."""

    def __init__(self, plan_file="nextGenSecurityPlanSteps.json"):
        """Initialize the Implementation Manager with the plan file."""
        self.plan_file = plan_file
        self.plan = self._load_plan()

    def _load_plan(self):
        """Load the implementation plan from the JSON file."""
        try:
            with open(self.plan_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Plan file '{self.plan_file}' not found.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Plan file '{self.plan_file}' contains invalid JSON.")
            sys.exit(1)

    def _save_plan(self):
        """Save the implementation plan to the JSON file."""
        with open(self.plan_file, 'w') as f:
            json.dump(self.plan, f, indent=2)
        print(f"Plan saved to '{self.plan_file}'.")

    def update_metrics(self):
        """Update the metrics in the plan."""
        completed = sum(1 for step in self.plan['steps'] if step['status'] == 'completed')
        total = len(self.plan['steps'])
        percentage = (completed / total) * 100 if total > 0 else 0

        self.plan['metrics'] = {
            'completedSteps': completed,
            'totalSteps': total,
            'percentageComplete': round(percentage, 2)
        }
        self.plan['lastUpdated'] = datetime.datetime.now().strftime("%Y-%m-%d")

    def display_plan(self):
        """Display the implementation plan in a tabular format."""
        headers = ["Step", "Title", "Status", "Est. Time (Days)", "Dependencies"]
        table_data = []

        for step in self.plan['steps']:
            deps = ", ".join(map(str, step['dependencies'])) if step['dependencies'] else "None"
            table_data.append([
                step['step'],
                step['title'],
                step['status'],
                step['estimatedTimeInDays'],
                deps
            ])

        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        print(f"\nProject: {self.plan['projectName']}")
        print(f"Version: {self.plan['version']}")
        print(f"Last Updated: {self.plan['lastUpdated']}")
        print(f"Completion: {self.plan['metrics']['percentageComplete']}% ({self.plan['metrics']['completedSteps']}/{self.plan['metrics']['totalSteps']} steps)")
        print(f"Total Estimated Time: {self.plan['totalEstimatedTimeInDays']} days")

    def show_step_details(self, step_number):
        """Display detailed information about a specific step."""
        try:
            step = next(s for s in self.plan['steps'] if s['step'] == step_number)
        except StopIteration:
            print(f"Error: Step {step_number} not found.")
            return

        print(f"\nSTEP {step['step']}: {step['title']}")
        print("-" * 60)
        print(f"Status: {step['status']}")
        print(f"Estimated Time: {step['estimatedTimeInDays']} days")
        if step['dependencies']:
            print(f"Dependencies: {', '.join(map(str, step['dependencies']))}")
        else:
            print("Dependencies: None")
        print("\nDescription:")
        print(step['description'])
        print("\nTasks:")
        for i, task in enumerate(step['tasks'], 1):
            print(f"  {i}. {task}")

    def update_step_status(self, step_number, status):
        """Update the status of a specific step."""
        valid_statuses = ['pending', 'in_progress', 'completed', 'blocked']
        if status not in valid_statuses:
            print(f"Error: Invalid status. Must be one of {valid_statuses}")
            return

        try:
            step = next(s for s in self.plan['steps'] if s['step'] == step_number)
        except StopIteration:
            print(f"Error: Step {step_number} not found.")
            return

        # Check if all dependencies are completed
        if status == 'in_progress':
            for dep in step['dependencies']:
                dep_step = next((s for s in self.plan['steps'] if s['step'] == dep), None)
                if dep_step and dep_step['status'] != 'completed':
                    print(f"Warning: Dependency step {dep} has not been completed.")
                    confirm = input("Do you want to continue anyway? (y/n): ")
                    if confirm.lower() != 'y':
                        return

        step['status'] = status
        print(f"Updated step {step_number} status to '{status}'.")
        self.update_metrics()
        self._save_plan()

    def add_note_to_step(self, step_number, note):
        """Add a note to a specific step."""
        try:
            step = next(s for s in self.plan['steps'] if s['step'] == step_number)
        except StopIteration:
            print(f"Error: Step {step_number} not found.")
            return

        if 'notes' not in step:
            step['notes'] = []

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        step['notes'].append({
            'timestamp': timestamp,
            'note': note
        })
        print(f"Added note to step {step_number}.")
        self._save_plan()

    def generate_report(self):
        """Generate a report on the implementation progress."""
        completed = [s for s in self.plan['steps'] if s['status'] == 'completed']
        in_progress = [s for s in self.plan['steps'] if s['status'] == 'in_progress']
        pending = [s for s in self.plan['steps'] if s['status'] == 'pending']
        blocked = [s for s in self.plan['steps'] if s['status'] == 'blocked']

        print("\n=== IMPLEMENTATION PROGRESS REPORT ===")
        print(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Project: {self.plan['projectName']}")
        print(f"Version: {self.plan['version']}")
        print(f"Last Updated: {self.plan['lastUpdated']}")
        print("-" * 40)
        print(f"Progress: {self.plan['metrics']['percentageComplete']}% completed")
        print(f"Completed Steps: {len(completed)}/{len(self.plan['steps'])}")
        print(f"In Progress Steps: {len(in_progress)}")
        print(f"Pending Steps: {len(pending)}")
        print(f"Blocked Steps: {len(blocked)}")
        print("-" * 40)

        if in_progress:
            print("\nCURRENT WORK IN PROGRESS:")
            for step in in_progress:
                print(f"  Step {step['step']}: {step['title']}")

        if blocked:
            print("\nBLOCKED STEPS (REQUIRE ATTENTION):")
            for step in blocked:
                print(f"  Step {step['step']}: {step['title']}")

        elapsed_days = sum(s['estimatedTimeInDays'] for s in completed)
        remaining_days = sum(s['estimatedTimeInDays'] for s in in_progress + pending + blocked)
        
        print("-" * 40)
        print(f"Estimated Days Completed: {elapsed_days}")
        print(f"Estimated Days Remaining: {remaining_days}")
        print(f"Total Estimated Days: {self.plan['totalEstimatedTimeInDays']}")


def main():
    """Main function to process command line arguments."""
    parser = argparse.ArgumentParser(description="Implementation Plan Manager for MyProject Security")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Show plan command
    subparsers.add_parser("show", help="Display the implementation plan")

    # Show step details command
    step_parser = subparsers.add_parser("step", help="Display details of a specific step")
    step_parser.add_argument("step_number", type=int, help="Step number to display")

    # Update step status command
    update_parser = subparsers.add_parser("update", help="Update the status of a step")
    update_parser.add_argument("step_number", type=int, help="Step number to update")
    update_parser.add_argument("status", choices=["pending", "in_progress", "completed", "blocked"],
                               help="New status for the step")

    # Add note command
    note_parser = subparsers.add_parser("note", help="Add a note to a step")
    note_parser.add_argument("step_number", type=int, help="Step number to add a note to")
    note_parser.add_argument("note", help="Note to add")

    # Generate report command
    subparsers.add_parser("report", help="Generate a progress report")

    args = parser.parse_args()
    
    manager = ImplementationManager()

    if args.command == "show" or not args.command:
        manager.display_plan()
    elif args.command == "step":
        manager.show_step_details(args.step_number)
    elif args.command == "update":
        manager.update_step_status(args.step_number, args.status)
    elif args.command == "note":
        manager.add_note_to_step(args.step_number, args.note)
    elif args.command == "report":
        manager.generate_report()


if __name__ == "__main__":
    main() 