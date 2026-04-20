const { error } = require('./core.cjs');

function cmdRequirementsMarkComplete() {
  error('requirements mark-complete not implemented in this workspace');
}

function cmdMilestoneComplete() {
  error('milestone complete not implemented in this workspace');
}

module.exports = {
  cmdRequirementsMarkComplete,
  cmdMilestoneComplete,
};

