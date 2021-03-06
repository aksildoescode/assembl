// @flow
import React from 'react';
/* eslint-disable import/no-extraneous-dependencies */
import { storiesOf } from '@storybook/react';
import { action } from '@storybook/addon-actions';
/* eslint-enable */

import FictionCommentForm from '../../../../components/debate/brightMirror/fictionCommentForm';
import type { FictionCommentFormProps } from '../../../../components/debate/brightMirror/fictionCommentForm';

const actions: { [name: string]: Function } = {
  onCancelCommentCallback: action('onCancelCommentCallback'),
  onSubmitCommentCallback: action('onSubmitCommentCallback')
};

export const defaultFictionCommentForm: FictionCommentFormProps = {
  onCancelCommentCallback: actions.onCancelCommentCallback,
  onSubmitCommentCallback: actions.onSubmitCommentCallback,
  rowsForTextarea: 2
};

const fictionCommentFormWithComment: FictionCommentFormProps = {
  ...defaultFictionCommentForm,
  commentValue: 'What\'s normal anyways?'
};

const fictionCommentFormInEditMode: FictionCommentFormProps = {
  ...defaultFictionCommentForm,
  commentValue: 'What\'s normal anyways?',
  editMode: true
};

storiesOf('FictionCommentForm', module)
  .add('default', () => <FictionCommentForm {...defaultFictionCommentForm} />)
  .add('with comment', () => <FictionCommentForm {...fictionCommentFormWithComment} />)
  .add('in edit mode', () => <FictionCommentForm {...fictionCommentFormInEditMode} />);