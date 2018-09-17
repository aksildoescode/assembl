// @flow
import React from 'react';
import { configure, mount } from 'enzyme';
import { MockedProvider } from 'react-apollo/test-utils';
import Adapter from 'enzyme-adapter-react-16';
// Graphql imports
import BrightMirrorFictionQuery from '../../../js/app/graphql/BrightMirrorFictionQuery.graphql';
// Containers import
import { BrightMirrorFiction } from '../../../js/app/pages/brightMirrorFiction';
// Components imports
import FictionHeader from '../../../js/app/components/debate/brightMirror/fictionHeader';
import FictionToolbar from '../../../js/app/components/debate/brightMirror/fictionToolbar';
import FictionBody from '../../../js/app/components/debate/brightMirror/fictionBody';
// Constant imports
import { PublicationStates } from '../../../js/app/constants';
// Type imports
import type { BrightMirrorFictionProps, BrightMirrorFictionData } from '../../../js/app/pages/brightMirrorFiction';

configure({ adapter: new Adapter() });

// Mock utils functions
jest.mock('../../../js/app/utils/utilityManager', () => ({ displayAlert: jest.fn() }));

const brightMirrorFictionPropsTemplate = {
  slug: 'voluptatem-veritatis-ea',
  phase: 'hic',
  themeId: 'nihil',
  fictionId: 'deleniti',
  contentLocale: 'en'
};

const brightMirrorFictionDataTemplate = {
  fiction: {
    subject: 'Hic quia eveniet cupiditate placeat laboriosam.',
    body: 'Odit mollitia natus ea iusto voluptatibus omnis pariatur tempore ipsum.',
    creationDate: new Date(),
    publicationState: PublicationStates.PUBLISHED,
    creator: {
      userId: 99999999,
      displayName: 'Wendy Quigley',
      isDeleted: false,
      image: {
        externalUrl: 'http://tyrese.info'
      }
    }
  }
};

describe('<BrightMirrorFiction /> - with mount', () => {
  let wrapper;
  let mocks;
  let brightMirrorFictionData: BrightMirrorFictionData;
  let brightMirrorFictionProps: BrightMirrorFictionProps;

  const displayNothing = () => {
    expect(wrapper.find(FictionBody)).toHaveLength(0);
    expect(wrapper.find(FictionToolbar)).toHaveLength(0);
    expect(wrapper.find(FictionBody)).toHaveLength(0);
  };

  describe('when loading is done without error', () => {
    beforeEach(() => {
      // Define props
      brightMirrorFictionData = {
        ...brightMirrorFictionDataTemplate,
        loading: false,
        error: null
      };

      brightMirrorFictionProps = {
        brightMirrorFictionData: brightMirrorFictionData,
        ...brightMirrorFictionPropsTemplate
      };

      // Mock Apollo
      mocks = [
        {
          request: { query: BrightMirrorFictionQuery },
          result: {
            data: brightMirrorFictionData
          }
        }
      ];

      wrapper = mount(
        <MockedProvider mocks={mocks}>
          <BrightMirrorFiction {...brightMirrorFictionProps} />
        </MockedProvider>
      );
    });

    it('should render a FictionHeader', () => {
      expect(wrapper.find(FictionHeader)).toHaveLength(1);
    });

    it('should render a FictionToolbar', () => {
      expect(wrapper.find(FictionToolbar)).toHaveLength(1);
    });

    it('should render a FictionBody', () => {
      expect(wrapper.find(FictionBody)).toHaveLength(1);
    });
  });

  describe('when loading is not done', () => {
    beforeEach(() => {
      // Define props
      brightMirrorFictionData = {
        ...brightMirrorFictionDataTemplate,
        loading: true, // set loading to true
        error: null
      };

      brightMirrorFictionProps = {
        brightMirrorFictionData: brightMirrorFictionData,
        ...brightMirrorFictionPropsTemplate
      };

      // Mock Apollo
      mocks = [
        {
          request: { query: BrightMirrorFictionQuery },
          result: {
            data: brightMirrorFictionData
          }
        }
      ];

      wrapper = mount(
        <MockedProvider mocks={mocks}>
          <BrightMirrorFiction {...brightMirrorFictionProps} />
        </MockedProvider>
      );
    });

    it('should display nothing', () => {
      displayNothing();
    });
  });

  describe('when there is a loading error', () => {
    beforeEach(() => {
      // Define props
      brightMirrorFictionData = {
        ...brightMirrorFictionDataTemplate,
        loading: false,
        error: { dummy: 'error' } // set loading error
      };

      brightMirrorFictionProps = {
        brightMirrorFictionData: brightMirrorFictionData,
        ...brightMirrorFictionPropsTemplate
      };

      // Mock Apollo
      mocks = [
        {
          request: { query: BrightMirrorFictionQuery },
          result: {
            data: brightMirrorFictionData
          }
        }
      ];

      wrapper = mount(
        <MockedProvider mocks={mocks}>
          <BrightMirrorFiction {...brightMirrorFictionProps} />
        </MockedProvider>
      );
    });

    it('should display nothing', () => {
      displayNothing();
    });
  });
});