// @flow
import * as React from 'react';
import { graphql, compose } from 'react-apollo';
import { connect } from 'react-redux';
import { Translate, I18n } from 'react-redux-i18n';
import { Grid, Col, Button } from 'react-bootstrap';
import { EditorState } from 'draft-js';

import { getConnectedUserId, getPostPublicationState } from '../../../utils/globalFunctions';
import { inviteUserToLogin, displayAlert } from '../../../utils/utilityManager';
import { connectedUserIsModerator } from '../../../utils/permissions';
import { SMALL_SCREEN_WIDTH, MINIMUM_BODY_LENGTH } from '../../../constants';
import { withScreenDimensions } from '../../common/screenDimensions';
import RichTextEditor from '../../common/richTextEditor';
import { convertEditorStateToHTML } from '../../../utils/draftjs';
import createPostMutation from '../../../graphql/mutations/createPost.graphql';
import { DebateContext } from '../../../app';

type Props = {
  isDebateModerated: boolean,
  isPhaseCompleted: boolean,
  title: string,
  contentLocale: string,
  questionId: string,
  scrollToQuestion: Function,
  index: number,
  refetchTheme: Function,
  mutate: Function,
  screenHeight: number,
  screenWidth: number,
  questionsLength: number
};

type State = {
  buttonDisabled: boolean,
  postBody: EditorState
};

export class Question extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      buttonDisabled: false,
      postBody: EditorState.createEmpty()
    };
  }

  createPost = () => {
    const { contentLocale, questionId, scrollToQuestion, index, refetchTheme, isDebateModerated } = this.props;
    const body = this.state.postBody;
    const userIsModerator = connectedUserIsModerator();
    const publicationState = getPostPublicationState(isDebateModerated, userIsModerator);
    displayAlert('success', I18n.t('loading.wait'), false, 10000);
    this.setState({ buttonDisabled: true }, () =>
      this.props
        .mutate({
          variables: {
            contentLocale: contentLocale,
            ideaId: questionId,
            body: convertEditorStateToHTML(body),
            publicationState: publicationState
          }
        })
        .then(() => {
          scrollToQuestion(true, index + 1);
          const successMessage = isDebateModerated && !userIsModerator ? 'postToBeValidated' : 'postSuccess';
          displayAlert('success', I18n.t(`debate.survey.${successMessage}`), false, 10000);
          refetchTheme();
          this.setState({
            postBody: EditorState.createEmpty(),
            buttonDisabled: false
          });
        })
        .catch((error) => {
          displayAlert('danger', error.message);
          this.setState({
            buttonDisabled: false
          });
        })
    );
  };

  updateBody = (newValue: EditorState) => {
    this.setState({
      postBody: newValue
    });
  };

  redirectToLogin = () => {
    const isUserConnected = getConnectedUserId();
    const { scrollToQuestion, index } = this.props;
    if (!isUserConnected) {
      inviteUserToLogin();
    } else {
      scrollToQuestion(true, index);
    }
  };

  getPostBodyCharCount = () => {
    const { postBody } = this.state;
    if (postBody) {
      return postBody.getCurrentContent().getPlainText().length;
    }

    return 0;
  };

  render() {
    const { index, isPhaseCompleted, title, screenWidth, screenHeight, questionsLength } = this.props;
    const questionTitle = questionsLength > 1 ? `${index}/ ${title}` : title;
    let height = screenHeight;
    const timelineElm = document && document.getElementById('timeline');
    // This is necessary to bypass an issue with Flow
    if (timelineElm) {
      height = screenHeight - timelineElm.clientHeight;
    }
    return (
      <section
        className={isPhaseCompleted ? 'hidden' : 'questions-section'}
        id={`q${index}`}
        style={screenWidth >= SMALL_SCREEN_WIDTH ? { height: height } : { height: '100%' }}
      >
        <Grid fluid className="background-grey">
          <div className="max-container">
            <div className="question-title">
              <div className="title-hyphen">&nbsp;</div>
              <h1 className="dark-title-5">{questionTitle}</h1>
            </div>
            <Col xs={12} md={9} className="col-centered">
              <RichTextEditor
                editorState={this.state.postBody}
                onChange={this.updateBody}
                placeHolder={I18n.t('debate.survey.txtAreaPh')}
                handleInputFocus={this.redirectToLogin}
              />
              <Button
                onClick={this.createPost}
                disabled={this.getPostBodyCharCount() > MINIMUM_BODY_LENGTH ? this.state.buttonDisabled : true}
                className={
                  this.getPostBodyCharCount() > MINIMUM_BODY_LENGTH
                    ? 'button-submit button-dark right margin-l clear'
                    : 'button-submit button-disable right margin-l clear'
                }
              >
                <Translate value="debate.survey.submit" />
              </Button>
            </Col>
          </div>
        </Grid>
      </section>
    );
  }
}

const mapStateToProps = state => ({
  contentLocale: state.i18n.locale
});

const QuestionWithContext = props => (
  <DebateContext.Consumer>
    {({ isDebateModerated }) => <Question {...props} isDebateModerated={isDebateModerated} />}
  </DebateContext.Consumer>
);

export default compose(connect(mapStateToProps), graphql(createPostMutation), withScreenDimensions)(QuestionWithContext);